-- Drop existing type if it exists to avoid conflicts
DROP TYPE IF EXISTS speed_range CASCADE;

-- Create a custom type to return min/max speeds and weighted average
CREATE TYPE speed_range AS (
    min_speed numeric,
    max_speed numeric,
    avg_speed_weighted numeric,
    total_points integer,
    included_points integer
);

-- FUNCTION: public.calculate_percentile_speeds(uuid, boolean, numeric)

-- DROP FUNCTION IF EXISTS public.calculate_percentile_speeds(uuid, boolean, numeric);

CREATE OR REPLACE FUNCTION public.calculate_percentile_speeds(
    trip_id uuid,
    isvalide boolean DEFAULT true,
    percentage_to_include numeric DEFAULT 90.0)
    RETURNS speed_range
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    result speed_range;
    lower_percentile numeric;
    upper_percentile numeric;
    total_speed_points integer;
    included_speed_points integer;
BEGIN
    -- Validate input percentage
    IF percentage_to_include <= 0 OR percentage_to_include > 100 THEN
        RAISE EXCEPTION 'Percentage must be between 0 and 100, got: %', percentage_to_include;
    END IF;
    
    -- Calculate percentile bounds
    -- For 90%, we exclude 5% from each end (5th to 95th percentile)
    lower_percentile := (100.0 - percentage_to_include) / 2.0;
    upper_percentile := 100.0 - lower_percentile;
    
    -- Calculate speeds between consecutive points and get percentiles
    WITH speed_calculations AS (
        -- Get consecutive points for each trip to calculate speed
        SELECT 
            "tripId",
            timestamp,
            lat,
            long,
            "isValid",
            -- Get previous point data using window functions
            LAG(lat) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_lat,
            LAG(long) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_long,
            LAG(timestamp) OVER (PARTITION BY "tripId" ORDER BY timestamp) as prev_timestamp
        FROM public."tripDetail"
        WHERE "tripId" = trip_id
          AND (
              CASE 
                  WHEN isvalide = TRUE THEN "isValid" = TRUE
                  ELSE TRUE  -- Take all points if isvalide = FALSE
              END
          )
    ),
    
    speed_with_values AS (
        -- Calculate speed and distance between consecutive points
        SELECT 
            "tripId",
            EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) as time_diff_seconds,
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
                    -- Calculate speed in km/h
                    ST_Distance(
                        ST_Point(prev_long, prev_lat)::geography,
                        ST_Point(long, lat)::geography
                    ) / EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) * 3.6
                ELSE NULL
            END as speed_kmh
        FROM speed_calculations
    ),
    
    valid_speeds AS (
        -- Filter out invalid speeds and apply basic noise filtering
        SELECT 
            speed_kmh,
            distance_meters
        FROM speed_with_values 
        WHERE speed_kmh IS NOT NULL 
          AND distance_meters IS NOT NULL
          AND speed_kmh >= 0  -- Non-negative speeds only
          AND distance_meters > 0  -- Valid distance
          AND time_diff_seconds >= 1  -- Minimum 1 second between points
    ),
    
    speed_percentiles AS (
        -- Calculate the percentiles
        SELECT 
            COUNT(*) as total_points,
            PERCENTILE_CONT(lower_percentile/100.0) WITHIN GROUP (ORDER BY speed_kmh)::numeric as min_speed_percentile,
            PERCENTILE_CONT(upper_percentile/100.0) WITHIN GROUP (ORDER BY speed_kmh)::numeric as max_speed_percentile
        FROM valid_speeds
    ),
    
    filtered_speeds AS (
        -- Get speeds and distances within the percentile range
        SELECT 
            vs.speed_kmh,
            vs.distance_meters,
            sp.min_speed_percentile,
            sp.max_speed_percentile,
            sp.total_points
        FROM valid_speeds vs
        CROSS JOIN speed_percentiles sp
        WHERE vs.speed_kmh >= sp.min_speed_percentile 
          AND vs.speed_kmh <= sp.max_speed_percentile
    )
    
    -- Get final results including distance-weighted average
    SELECT 
        ROUND(min_speed_percentile, 2) as min_speed,
        ROUND(max_speed_percentile, 2) as max_speed,
        CASE 
            WHEN SUM(distance_meters) > 0 THEN
                ROUND((SUM(speed_kmh * distance_meters) / NULLIF(SUM(distance_meters), 0))::numeric, 2)
            ELSE NULL
        END as avg_speed_weighted,
        total_points::integer,
        COUNT(*)::integer as included_points
    INTO result
    FROM filtered_speeds
    GROUP BY min_speed_percentile, max_speed_percentile, total_points;
    
    -- Handle case where no valid speeds found
    IF result.total_points IS NULL OR result.total_points = 0 THEN
        result.min_speed := NULL;
        result.max_speed := NULL;
        result.avg_speed_weighted := NULL;
        result.total_points := 0;
        result.included_points := 0;
    END IF;
    
    RETURN result;
END;
$BODY$;

ALTER FUNCTION public.calculate_percentile_speeds(uuid, boolean, numeric)
    OWNER TO psqladminun;

-- Helper function to get just min/max as separate values
CREATE OR REPLACE FUNCTION public.get_trip_speed_range(
    trip_id uuid,
    isvalide boolean DEFAULT true,
    percentage_to_include numeric DEFAULT 90.0)
    RETURNS TABLE(min_speed numeric, max_speed numeric)
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
    speed_data speed_range;
BEGIN
    SELECT * INTO speed_data 
    FROM calculate_percentile_speeds(trip_id, isvalide, percentage_to_include);
    
    RETURN QUERY SELECT speed_data.min_speed, speed_data.max_speed;
END;
$BODY$;

ALTER FUNCTION public.get_trip_speed_range(uuid, boolean, numeric)
    OWNER TO psqladminun;

-- Helper function to get min/max speeds and weighted average
CREATE OR REPLACE FUNCTION public.get_trip_speed_summary(
    trip_id uuid,
    isvalide boolean DEFAULT true,
    percentage_to_include numeric DEFAULT 90.0)
    RETURNS TABLE(min_speed numeric, max_speed numeric, avg_speed_weighted numeric)
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
    speed_data speed_range;
BEGIN
    SELECT * INTO speed_data 
    FROM calculate_percentile_speeds(trip_id, isvalide, percentage_to_include);
    
    RETURN QUERY SELECT speed_data.min_speed, speed_data.max_speed, speed_data.avg_speed_weighted;
END;
$BODY$;

ALTER FUNCTION public.get_trip_speed_summary(uuid, boolean, numeric)
    OWNER TO psqladminun;