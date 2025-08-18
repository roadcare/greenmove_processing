-- FUNCTION: public.update_trip_detail_invalid_speed_jumps(uuid, numeric, numeric, numeric)
-- Marks tripDetail points as invalid when they have:
-- 1. Excessive acceleration (> max_acceleration_ms2)
-- 2. Excessive deceleration (> max_deceleration_ms2)
-- 3. Speed exceeding max_speed_kmh
-- 4. GPS unreliability: accuracy > 50m or heading = -1

-- DROP FUNCTION IF EXISTS public.update_trip_detail_invalid_speed_jumps(uuid, numeric, numeric, numeric);

CREATE OR REPLACE FUNCTION public.update_trip_detail_invalid_speed_jumps(
    trip_id uuid,
    max_acceleration_ms2 numeric DEFAULT 15.0,  -- Max acceleration in m/s² (default: very permissive)
    max_deceleration_ms2 numeric DEFAULT 15.0,  -- Max deceleration in m/s² (default: very permissive)
    max_speed_kmh numeric DEFAULT 1500.0        -- Max realistic speed in km/h (covers all vehicles including planes)
)
    RETURNS TABLE(
        total_points integer,
        points_marked_invalid integer,
        points_already_invalid integer,
        points_valid integer
    )
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    v_total_points integer;
    v_points_marked_invalid integer;
    v_points_already_invalid integer;
    v_points_valid integer;
BEGIN
    -- Create temporary table to store points that should be marked invalid
    CREATE TEMP TABLE temp_invalid_points AS
    WITH     speed_calculations AS (
        -- Get consecutive points for each trip to calculate speed
        SELECT 
            "tripId",
            timestamp,
            lat,
            long,
            "isValid",
            accuracy,
            heading,
            -- Get previous point data using window functions
            LAG(lat) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_lat,
            LAG(long) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_long,
            LAG(timestamp) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_timestamp
        FROM public."tripDetail"
        WHERE "tripId" = trip_id
    ),
    
    speed_with_values AS (
        -- Calculate speed and distance between consecutive points
        SELECT 
            "tripId",
            timestamp,
            lat,
            long,
            "isValid",
            accuracy,
            heading,
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
    ),
    
    points_to_invalidate AS (
        -- Identify points that should be marked as invalid
        SELECT 
            "tripId",
            timestamp,
            speed_kmh,
            distance_meters,
            time_seconds,
            accuracy,
            heading,
            "isValid",
            -- Calculate acceleration in m/s²
            CASE 
                WHEN prev_speed_ms IS NOT NULL AND time_seconds > 0 THEN
                    (speed_ms - prev_speed_ms) / time_seconds
                ELSE NULL
            END as acceleration_ms2,
            -- Determine if point should be invalid due to unrealistic speed changes
            CASE
                WHEN speed_kmh IS NULL THEN FALSE  -- Can't determine, keep current state
                WHEN speed_kmh > max_speed_kmh THEN TRUE  -- Exceeds max speed
                WHEN prev_speed_ms IS NOT NULL AND time_seconds > 0 THEN
                    -- Check acceleration/deceleration limits
                    CASE 
                        WHEN (speed_ms - prev_speed_ms) / time_seconds > max_acceleration_ms2 THEN TRUE  -- Too much acceleration
                        WHEN (speed_ms - prev_speed_ms) / time_seconds < -max_deceleration_ms2 THEN TRUE  -- Too much deceleration
                        ELSE FALSE
                    END
                ELSE FALSE
            END as should_be_invalid,
            -- GPS unreliable check based on accuracy and heading
            CASE
                WHEN accuracy > 50 THEN TRUE           -- GPS accuracy worse than 50 meters
                WHEN heading = -1 THEN TRUE             -- Invalid heading indicates bad GPS signal
                ELSE FALSE
            END as gps_unreliable,
            -- Reason for invalidation (for debugging/logging)
            CASE
                WHEN accuracy > 50 THEN 'GPS unreliable: accuracy ' || ROUND(accuracy::numeric, 1) || 'm > 50m threshold'
                WHEN heading = -1 THEN 'GPS unreliable: invalid heading (-1)'
                WHEN speed_kmh > max_speed_kmh THEN 'Exceeds max speed: ' || ROUND(speed_kmh::numeric, 2) || ' km/h'
                WHEN prev_speed_ms IS NOT NULL AND time_seconds > 0 AND 
                     (speed_ms - prev_speed_ms) / time_seconds > max_acceleration_ms2 
                THEN 'Excessive acceleration: ' || ROUND(((speed_ms - prev_speed_ms) / time_seconds)::numeric, 2) || ' m/s²'
                WHEN prev_speed_ms IS NOT NULL AND time_seconds > 0 AND 
                     (speed_ms - prev_speed_ms) / time_seconds < -max_deceleration_ms2 
                THEN 'Excessive deceleration: ' || ROUND(((speed_ms - prev_speed_ms) / time_seconds)::numeric, 2) || ' m/s²'
                ELSE NULL
            END as invalidation_reason
        FROM speed_with_acceleration
    )
    -- Select points that need to be invalidated
    SELECT 
        "tripId",
        timestamp,
        invalidation_reason,
        speed_kmh,
        acceleration_ms2
    FROM points_to_invalidate
    WHERE (should_be_invalid = TRUE OR gps_unreliable = TRUE)
      AND "isValid" = TRUE;  -- Only select points that are currently valid

    -- Get statistics before update
    SELECT COUNT(*) INTO v_total_points
    FROM public."tripDetail"
    WHERE "tripId" = trip_id;

    SELECT COUNT(*) INTO v_points_already_invalid
    FROM public."tripDetail"
    WHERE "tripId" = trip_id AND "isValid" = FALSE;

    -- Count points that will be marked invalid
    SELECT COUNT(*) INTO v_points_marked_invalid
    FROM temp_invalid_points;

    -- Update the tripDetail table to mark invalid points
    UPDATE public."tripDetail" td
    SET "isValid" = FALSE
    FROM temp_invalid_points tip
    WHERE td."tripId" = tip."tripId"
      AND td.timestamp = tip.timestamp;

    -- Calculate remaining valid points
    v_points_valid := v_total_points - v_points_already_invalid - v_points_marked_invalid;

    -- Optional: Log details about invalidated points for debugging
    -- You can uncomment this to see details in the PostgreSQL logs
    /*
    FOR r IN SELECT * FROM temp_invalid_points LIMIT 10
    LOOP
        RAISE NOTICE 'Invalidated point at %: % (speed: % km/h, acceleration: % m/s²)', 
            r.timestamp, r.invalidation_reason, 
            ROUND(r.speed_kmh::numeric, 2), 
            ROUND(COALESCE(r.acceleration_ms2, 0)::numeric, 2);
    END LOOP;
    */

    -- Drop temporary table
    DROP TABLE temp_invalid_points;

    -- Return statistics
    RETURN QUERY
    SELECT 
        v_total_points,
        v_points_marked_invalid,
        v_points_already_invalid,
        v_points_valid;
END;
$BODY$;

ALTER FUNCTION public.update_trip_detail_invalid_speed_jumps(uuid, numeric, numeric, numeric)
    OWNER TO psqladminun;

-- Example usage:
-- Update with default thresholds (15 m/s² acceleration/deceleration, 1500 km/h max speed)
-- SELECT * FROM update_trip_detail_invalid_speed_jumps('trip-uuid-here');

-- Update with custom thresholds for walking/running
-- SELECT * FROM update_trip_detail_invalid_speed_jumps('trip-uuid-here', 2.0, 2.0, 15.0);

-- Update with custom thresholds for car
-- SELECT * FROM update_trip_detail_invalid_speed_jumps('trip-uuid-here', 5.0, 8.0, 200.0);

-- Note: Points with accuracy > 50m or heading = -1 will also be marked as invalid regardless of thresholds

-- To see what would be invalidated without actually updating (dry run):
-- You can create a similar function that only returns the points that would be invalidated
-- without performing the UPDATE operation

-- Batch update all trips in the system (use with caution):
/*
DO $$
DECLARE
    trip_record RECORD;
    update_result RECORD;
BEGIN
    FOR trip_record IN SELECT id, vehicle FROM public.trip
    LOOP
        -- Use different thresholds based on vehicle type
        CASE trip_record.vehicle
            WHEN 'walking' THEN
                SELECT * INTO update_result FROM update_trip_detail_invalid_speed_jumps(trip_record.id, 2.0, 2.0, 15.0);
            WHEN 'running' THEN
                SELECT * INTO update_result FROM update_trip_detail_invalid_speed_jumps(trip_record.id, 3.0, 3.0, 25.0);
            WHEN 'bicycle' THEN
                SELECT * INTO update_result FROM update_trip_detail_invalid_speed_jumps(trip_record.id, 3.0, 4.0, 60.0);
            WHEN 'car' THEN
                SELECT * INTO update_result FROM update_trip_detail_invalid_speed_jumps(trip_record.id, 5.0, 8.0, 200.0);
            WHEN 'train' THEN
                SELECT * INTO update_result FROM update_trip_detail_invalid_speed_jumps(trip_record.id, 2.0, 3.0, 300.0);
            WHEN 'plane' THEN
                SELECT * INTO update_result FROM update_trip_detail_invalid_speed_jumps(trip_record.id, 3.0, 2.0, 900.0);
            ELSE
                SELECT * INTO update_result FROM update_trip_detail_invalid_speed_jumps(trip_record.id);
        END CASE;
        
        IF update_result.points_marked_invalid > 0 THEN
            RAISE NOTICE 'Trip %: marked % points as invalid', 
                trip_record.id, update_result.points_marked_invalid;
        END IF;
    END LOOP;
END $$;
*/