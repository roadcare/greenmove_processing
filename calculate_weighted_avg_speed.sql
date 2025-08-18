-- FUNCTION: public.calculate_weighted_avg_speed(uuid, boolean, numeric, numeric, numeric)

-- DROP FUNCTION IF EXISTS public.calculate_weighted_avg_speed(uuid, boolean, numeric, numeric, numeric);

CREATE OR REPLACE FUNCTION public.calculate_weighted_avg_speed(
    trip_id uuid,
    isfiltervalide boolean DEFAULT false,
    max_acceleration_ms2 numeric DEFAULT 15.0,  -- Max acceleration in m/s² (default: very permissive)
    max_deceleration_ms2 numeric DEFAULT 15.0,  -- Max deceleration in m/s² (default: very permissive)
    max_speed_kmh numeric DEFAULT 1500.0       -- Max realistic speed in km/h (covers all vehicles including planes)
)
    RETURNS numeric
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    weighted_avg_speed NUMERIC;
BEGIN
    -- Calculate distance-weighted average speed with acceleration filtering
    WITH speed_calculations AS (
        -- Get consecutive points for each trip to calculate speed
        SELECT 
            "tripId",
            timestamp,
            lat,
            long,
            "isValid",
            accuracy,
            -- Get previous point data using window functions
            LAG(lat) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_lat,
            LAG(long) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_long,
            LAG(timestamp) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_timestamp,
            LAG(accuracy) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_accuracy
        FROM public."tripDetail"
        WHERE "tripId" = trip_id
          AND (
              CASE 
                  WHEN isFilterValide = TRUE THEN "isValid" = TRUE
                  ELSE TRUE  -- Take all points if isFilterValide = FALSE
              END
          )
    ),
    
    speed_with_values AS (
        -- Calculate speed and distance between consecutive points
        SELECT 
            "tripId",
            timestamp,
            prev_timestamp,
            lat,
            long,
            accuracy,
            prev_accuracy,
            CASE 
                WHEN prev_lat IS NOT NULL 
                     AND prev_long IS NOT NULL 
                     AND prev_timestamp IS NOT NULL
                     AND EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) > 0
                THEN 
                    -- Calculate distance in meters
                    ST_Distance(
                        ST_Point(prev_long, prev_lat)::geography,
                        ST_Point(long, lat)::geography
                    )
                ELSE NULL
            END as distance_meters,
            CASE 
                WHEN prev_lat IS NOT NULL 
                     AND prev_long IS NOT NULL 
                     AND prev_timestamp IS NOT NULL
                     AND EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) > 0
                THEN 
                    -- Calculate time difference in seconds
                    EXTRACT(EPOCH FROM (timestamp - prev_timestamp))
                ELSE NULL
            END as time_seconds,
            CASE 
                WHEN prev_lat IS NOT NULL 
                     AND prev_long IS NOT NULL 
                     AND prev_timestamp IS NOT NULL
                     AND EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) > 0
                THEN 
                    -- Calculate speed in km/h
                    ST_Distance(
                        ST_Point(prev_long, prev_lat)::geography,
                        ST_Point(long, lat)::geography
                    ) / EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) * 3.6
                ELSE NULL
            END as speed_kmh
        FROM speed_calculations
    ),
    
    speed_with_acceleration AS (
        -- Calculate acceleration between consecutive segments
        SELECT 
            *,
            -- Get previous speed for acceleration calculation
            LAG(speed_kmh) OVER (ORDER BY timestamp) as prev_speed_kmh,
            -- Calculate speed in m/s for acceleration calculation
            speed_kmh / 3.6 as speed_ms,
            LAG(speed_kmh / 3.6) OVER (ORDER BY timestamp) as prev_speed_ms
        FROM speed_with_values
        WHERE speed_kmh IS NOT NULL
    ),
    
    filtered_speeds AS (
        -- Filter out unrealistic accelerations/decelerations
        SELECT 
            speed_kmh,
            distance_meters,
            time_seconds,
            accuracy,
            prev_accuracy,
            -- Calculate acceleration in m/s²
            CASE 
                WHEN prev_speed_ms IS NOT NULL AND time_seconds > 0 THEN
                    (speed_ms - prev_speed_ms) / time_seconds
                ELSE NULL
            END as acceleration_ms2,
            -- Flag for realistic speed change
            CASE
                WHEN prev_speed_ms IS NULL THEN TRUE  -- First segment is always valid
                WHEN time_seconds IS NULL OR time_seconds <= 0 THEN FALSE  -- Invalid time
                WHEN speed_kmh > max_speed_kmh THEN FALSE  -- Exceeds max speed
                WHEN prev_speed_ms IS NOT NULL AND time_seconds > 0 THEN
                    -- Check acceleration/deceleration limits
                    CASE 
                        WHEN (speed_ms - prev_speed_ms) / time_seconds > max_acceleration_ms2 THEN FALSE  -- Too much acceleration
                        WHEN (speed_ms - prev_speed_ms) / time_seconds < -max_deceleration_ms2 THEN FALSE  -- Too much deceleration
                        ELSE TRUE
                    END
                ELSE TRUE
            END as is_realistic,
            -- Additional filter for GPS accuracy if available
            CASE
                WHEN accuracy IS NOT NULL AND prev_accuracy IS NOT NULL THEN
                    -- If combined GPS uncertainty is greater than distance traveled, it's unreliable
                    CASE 
                        WHEN (accuracy + COALESCE(prev_accuracy, 0)) > distance_meters * 2 
                             AND distance_meters < 50  -- Only apply for short distances
                        THEN FALSE
                        ELSE TRUE
                    END
                ELSE TRUE
            END as is_gps_reliable
        FROM speed_with_acceleration
    ),
    
    moving_speeds AS (
        -- Take only realistic speeds and distances
        SELECT 
            speed_kmh,
            distance_meters,
            acceleration_ms2
        FROM filtered_speeds 
        WHERE speed_kmh IS NOT NULL 
          AND distance_meters > 0
          AND is_realistic = TRUE
          AND is_gps_reliable = TRUE
    )
    
    -- Calculate distance-weighted average
    SELECT 
        CASE 
            WHEN SUM(distance_meters) > 0 THEN
                ROUND((SUM(speed_kmh * distance_meters) / NULLIF(SUM(distance_meters), 0))::numeric, 2)
            ELSE NULL
        END
    INTO weighted_avg_speed
    FROM moving_speeds;
    
    -- Optional: Log filtering statistics for debugging
    -- RAISE NOTICE 'Filtered % unrealistic points out of % total points', 
    --     (SELECT COUNT(*) FROM filtered_speeds WHERE is_realistic = FALSE OR is_gps_reliable = FALSE),
    --     (SELECT COUNT(*) FROM filtered_speeds);
    
    RETURN weighted_avg_speed;
END;
$BODY$;

ALTER FUNCTION public.calculate_weighted_avg_speed(uuid, boolean, numeric, numeric, numeric)
    OWNER TO psqladminun;

-- Example usage:
-- Default filtering (15 m/s² acceleration, 15 m/s² deceleration, 1500 km/h max speed - covers all vehicle types)
-- SELECT calculate_weighted_avg_speed('trip-uuid-here', true);

-- Custom filtering for different vehicle types:
-- Walking/Running (lower thresholds)
-- SELECT calculate_weighted_avg_speed('trip-uuid-here', true, 2.0, 2.0, 15.0);

-- Bicycle
-- SELECT calculate_weighted_avg_speed('trip-uuid-here', true, 3.0, 4.0, 50.0);

-- Car
-- SELECT calculate_weighted_avg_speed('trip-uuid-here', true, 5.0, 8.0, 200.0);

-- Train (can have higher speeds but gentler acceleration)
-- SELECT calculate_weighted_avg_speed('trip-uuid-here', true, 2.0, 3.0, 300.0);

-- Plane (high speeds with moderate acceleration)
-- SELECT calculate_weighted_avg_speed('trip-uuid-here', true, 3.0, 2.0, 900.0);