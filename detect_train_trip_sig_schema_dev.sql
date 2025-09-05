-- FUNCTION: public.detect_train_trip_sig_schema(uuid, text, real, real, real, real, real)

-- DROP FUNCTION IF EXISTS public.detect_train_trip_sig_schema(uuid, text, real, real, real, real, real);

CREATE OR REPLACE FUNCTION public.detect_train_trip_sig_schema(
	trip_id uuid,
	schema_name text DEFAULT 'public'::text,
	min_train_distance real DEFAULT 0.5,
	min_train_ratio real DEFAULT 0.5,
	min_metro_length_ratio real DEFAULT 0.18,
	min_train_speed real DEFAULT 15,
	distance_to_train real DEFAULT 80)
    RETURNS boolean
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    total_distance REAL;
    avg_speed REAL;
    train_length REAL := 0;
    total_train_length REAL := 0;
    start_point_distance REAL;
    end_point_distance REAL;
    sql_query TEXT;
BEGIN
    -- Get the total distance and average speed of the trip using dynamic schema
    sql_query := format('SELECT "totalDistance", "avgSpeed" FROM %I.trip WHERE id = $1', schema_name);
    EXECUTE sql_query INTO total_distance, avg_speed USING trip_id;
    
    -- If trip not found, return false
    IF total_distance IS NULL OR avg_speed IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Calculate train_length, total_train_length and distances from start/end points to train buffer
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
        ),
        start_end_points AS (
            SELECT 
                (SELECT geom FROM trip_points WHERE rn = 1) as start_geom,
                (SELECT geom FROM trip_points WHERE rn = (SELECT MAX(rn) FROM trip_points)) as end_geom
        )
        SELECT 
            COALESCE(SUM(ST_Distance(geom1, geom2) / 1000.0), 0) as consecutive_train_length,
            (SELECT COALESCE(SUM(ST_Distance(geom1, geom2) / 1000.0), 0) FROM all_train_segments) as total_train_length,
            (SELECT COALESCE(MIN(ST_Distance(start_geom, tb.geom)), 999999) FROM bdtopo.train_buffer tb, start_end_points) as start_distance,
            (SELECT COALESCE(MIN(ST_Distance(end_geom, tb.geom)), 999999) FROM bdtopo.train_buffer tb, start_end_points) as end_distance
        FROM consecutive_in_train_segments
    ', schema_name);
    
    EXECUTE sql_query INTO train_length, total_train_length, start_point_distance, end_point_distance USING trip_id;
    
    -- Log the calculated values
    RAISE NOTICE 'Schema: %, Trip ID: %, Total Distance: % km, Avg Speed: % km/h, Train Length (consecutive): % km, Total Train Length (all): % km, Start Point Distance to Train: % m, End Point Distance to Train: % m, Min Train Ratio: %, Min Metro Length Ratio: %, Min Train Distance: % km, Min Train Speed: % km/h, Distance to Train: % m', 
        schema_name, trip_id, total_distance, avg_speed, train_length, total_train_length, start_point_distance, end_point_distance, min_train_ratio, min_metro_length_ratio, min_train_distance, min_train_speed, distance_to_train;
    
    -- Apply logic based on consecutive train_length ratio
    IF train_length > (min_train_ratio * total_distance) THEN
        -- High train coverage: check minimum distance and average speed > min_train_speed
        RETURN (total_distance > min_train_distance) AND (avg_speed > min_train_speed);
               
    ELSIF train_length <= (min_train_ratio * total_distance) AND train_length >= (min_metro_length_ratio * total_distance) THEN
        -- Medium train coverage: check start/end points proximity to train buffer AND average speed > min_train_speed
        RETURN (start_point_distance < distance_to_train AND end_point_distance < distance_to_train AND avg_speed > min_train_speed AND total_distance > min_train_distance);
        
    ELSE
        -- Low train coverage: return false
        RETURN FALSE;
    END IF;
END;
$BODY$;

ALTER FUNCTION public.detect_train_trip_sig_schema(uuid, text, real, real, real, real, real)
    OWNER TO psqladminun;
