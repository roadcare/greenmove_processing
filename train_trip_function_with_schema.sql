CREATE OR REPLACE FUNCTION detect_train_trip_sig_schema(
    trip_id UUID, 
    schema_name TEXT DEFAULT 'public',
    min_train_distance REAL DEFAULT 1.5,
    invalid_ratio_threshold REAL DEFAULT 0.6,
    min_train_ratio REAL DEFAULT 0.5,
    min_metro_length_ratio REAL DEFAULT 0.18
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    total_distance REAL;
    train_length REAL := 0;
    total_train_length REAL := 0;
    invalid_points INTEGER;
    calculated_invalid_ratio REAL;
    sql_query TEXT;
BEGIN
    -- Get the total distance of the trip using dynamic schema
    sql_query := format('SELECT "totalDistance" FROM %I.trip WHERE id = $1', schema_name);
    EXECUTE sql_query INTO total_distance USING trip_id;
    
    -- If trip not found, return false
    IF total_distance IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Calculate invalid_ratio by counting invalid points
    sql_query := format('
        SELECT COUNT(*)
        FROM %I."tripDetail" td
        WHERE td."tripId" = $1 AND td."isValid" = false
    ', schema_name);
    
    EXECUTE sql_query INTO invalid_points USING trip_id;
    
    -- Calculate invalid ratio (invalid points / total distance)
    calculated_invalid_ratio := invalid_points::REAL / total_distance;
    
    -- Calculate both train_length (consecutive in-train segments) and total_train_length (all in-train segments)
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
        ),
        trip_intrain_points AS (
            SELECT 
                geom,
                ROW_NUMBER() OVER (ORDER BY timestamp) as train_rn
            FROM trip_points
            WHERE is_in_train = true
        ),
        all_train_segments AS (
            SELECT 
                p1.geom as geom1,
                p2.geom as geom2
            FROM trip_intrain_points p1
            JOIN trip_intrain_points p2 ON p2.train_rn = p1.train_rn + 1
        )
        SELECT 
            COALESCE(SUM(ST_Distance(geom1, geom2) / 1000.0), 0) as consecutive_train_length,
            (SELECT COALESCE(SUM(ST_Distance(geom1, geom2) / 1000.0), 0) FROM all_train_segments) as total_train_length
        FROM consecutive_in_train_segments
    ', schema_name);
    
    EXECUTE sql_query INTO train_length, total_train_length USING trip_id;
    
    -- Log the calculated values
    RAISE NOTICE 'Schema: %, Trip ID: %, Total Distance: % km, Train Length (consecutive): % km, Total Train Length (all): % km, Calculated Invalid Ratio: %, Invalid Ratio Threshold: %, Min Train Ratio: %, Min Metro Length Ratio: %, Min Train Distance: % km', 
        schema_name, trip_id, total_distance, train_length, total_train_length, calculated_invalid_ratio, invalid_ratio_threshold, min_train_ratio, min_metro_length_ratio, min_train_distance;
    
    -- Apply different conditions based on calculated_invalid_ratio vs threshold
    IF calculated_invalid_ratio > invalid_ratio_threshold THEN
        -- More lenient condition when calculated_invalid_ratio > threshold (poor GPS) - use total_train_length
        RETURN ((total_train_length > (min_metro_length_ratio * total_distance)) OR (total_train_length > 4.0)) AND (total_distance > min_train_distance);
    ELSE
        -- Modified condition when calculated_invalid_ratio <= threshold (good GPS) - use train_length
        RETURN ((train_length > (min_train_ratio * total_distance)) OR (train_length > 8.0)) AND (total_distance > min_train_distance);
    END IF;
END;
$$;

-- Example usage:
-- SELECT detect_train_trip_sig_schema('your-trip-uuid'::uuid);
-- SELECT detect_train_trip_sig_schema('your-trip-uuid'::uuid, 'public', 1.5, 0.7, 0.4, 0.15);
-- 
-- Parameters:
-- trip_id: UUID of the trip to analyze
-- schema_name: Database schema name (default: 'public')
-- min_train_distance: Minimum trip distance to consider (default: 1.5 km)
-- invalid_ratio_threshold: Threshold for switching between strict/lenient conditions (default: 0.6)
-- min_train_ratio: Minimum ratio of train_length to total_distance for good GPS (default: 0.5)
-- min_metro_length_ratio: Minimum ratio of train_length to total_distance for poor GPS (default: 0.18)