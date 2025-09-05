CREATE OR REPLACE FUNCTION calculate_consecutive_train_length_km(
    trip_id UUID, 
    schema_name TEXT DEFAULT 'public'
)
RETURNS REAL
LANGUAGE plpgsql
AS $$
DECLARE
    train_length REAL := 0;
    sql_query TEXT;
BEGIN
    -- Calculate train_length (consecutive in-train segments)
    sql_query := format('
        WITH trip_points AS (
            SELECT 
                td.timestamp,
                td.long,
                td.lat,
                ST_Transform(ST_SetSRID(ST_MakePoint(td.long, td.lat), 4326), 2154) as geom,
                -- Check if point is within any train buffer
                EXISTS (
                    SELECT 1 
                    FROM bdtopo.train_buffer tb 
                    WHERE ST_Within(
                        ST_Transform(ST_SetSRID(ST_MakePoint(td.long, td.lat), 4326), 2154), 
                        tb.geom
                    )
                ) as is_in_train,
                ROW_NUMBER() OVER (ORDER BY td.timestamp) as rn
            FROM %I."tripDetail" td
            WHERE td."tripId" = $1             
            ORDER BY td.timestamp
        ),
        consecutive_in_train_segments AS (
            SELECT 
                p1.geom as geom1,
                p2.geom as geom2
            FROM trip_points p1
            JOIN trip_points p2 ON p2.rn = p1.rn + 1
            WHERE p1.is_in_train = true AND p2.is_in_train = true
        )
        SELECT 
            COALESCE(SUM(ST_Distance(geom1, geom2) / 1000.0), 0) as consecutive_train_length
        FROM consecutive_in_train_segments
    ', schema_name);
    
    EXECUTE sql_query INTO train_length USING trip_id;
    
    -- Return the consecutive train length in kilometers
    RETURN COALESCE(train_length, 0);
    
EXCEPTION
    WHEN OTHERS THEN
        -- Log error and return 0
        RAISE NOTICE 'Error calculating consecutive train length for trip %: %', trip_id, SQLERRM;
        RETURN 0;
END;
$$;

-- Example usage:
-- SELECT calculate_consecutive_train_length_km('your-trip-uuid'::uuid);
-- SELECT calculate_consecutive_train_length_km('your-trip-uuid'::uuid, 'public');
-- 
-- Use with trip data:
-- SELECT 
--     t.id,
--     t."totalDistance" as total_distance_km,
--     calculate_consecutive_train_length_km(t.id) as consecutive_train_length_km,
--     calculate_consecutive_train_length_km(t.id) / t."totalDistance" as consecutive_train_ratio
-- FROM public.trip t 
-- WHERE t.id = 'your-trip-uuid'::uuid;