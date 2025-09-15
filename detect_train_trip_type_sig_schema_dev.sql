CREATE OR REPLACE FUNCTION public.detect_train_trip_type_sig_schema_dev(
    trip_id uuid,
    schema_name text DEFAULT 'public'::text,
    min_train_distance real DEFAULT 0.5,
    min_train_ratio real DEFAULT 0.5,
    min_metro_length_ratio real DEFAULT 0.18,
    min_train_speed real DEFAULT 15,
    distance_to_train real DEFAULT 80)
    RETURNS text
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
    intersecting_nature TEXT;
    start_end_nature TEXT;
    sql_query TEXT;
BEGIN
    -- Get the total distance and average speed of the trip using dynamic schema
    sql_query := format('SELECT "totalDistance", "avgSpeed" FROM %I.trip WHERE id = $1', schema_name);
    EXECUTE sql_query INTO total_distance, avg_speed USING trip_id;
    
    -- If trip not found, return NOT_TRAIN
    IF total_distance IS NULL OR avg_speed IS NULL THEN
        RETURN 'NOT_TRAIN';
    END IF;
    
    -- Calculate train_length, total_train_length, distances from start/end points to train buffer, and get intersecting natures
    sql_query := format('
        WITH trip_points AS (
            SELECT 
                td.timestamp,
                td.long,
                td.lat,
                ST_Transform(ST_SetSRID(ST_MakePoint(td.long, td.lat), 4326), 2154) as geom,
                -- Check if point is within any train buffer and get the nature
                (
                    SELECT tb.nature 
                    FROM bdtopo.trains_buffer tb 
                    WHERE ST_Within(
                        ST_Transform(ST_SetSRID(ST_MakePoint(td.long, td.lat), 4326), 2154), 
                        tb.geom
                    )
                    LIMIT 1
                ) as train_nature,
                -- Check if point is within any train buffer
                EXISTS (
                    SELECT 1 
                    FROM bdtopo.trains_buffer tb 
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
                p2.geom as geom2,
                COALESCE(p1.train_nature, p2.train_nature) as segment_nature
            FROM trip_points p1
            JOIN trip_points p2 ON p2.rn = p1.rn + 1
            WHERE p1.is_in_train = true AND p2.is_in_train = true
        ),
        trip_intrain_points AS (
            SELECT 
                geom,
                train_nature,
                ROW_NUMBER() OVER (ORDER BY timestamp) as train_rn
            FROM trip_points
            WHERE is_in_train = true
        ),
        all_train_segments AS (
            SELECT 
                p1.geom as geom1,
                p2.geom as geom2,
                COALESCE(p1.train_nature, p2.train_nature) as segment_nature
            FROM trip_intrain_points p1
            JOIN trip_intrain_points p2 ON p2.train_rn = p1.train_rn + 1
        ),
        start_end_points AS (
            SELECT 
                (SELECT geom FROM trip_points WHERE rn = 1) as start_geom,
                (SELECT geom FROM trip_points WHERE rn = (SELECT MAX(rn) FROM trip_points)) as end_geom
        ),
        most_common_intersecting_nature AS (
            SELECT 
                segment_nature,
                COUNT(*) as frequency
            FROM consecutive_in_train_segments
            WHERE segment_nature IS NOT NULL
            GROUP BY segment_nature
            ORDER BY frequency DESC, segment_nature
            LIMIT 1
        ),
        nearest_start_end_nature AS (
            SELECT 
                tb.nature,
                MIN(LEAST(
                    ST_Distance(sep.start_geom, tb.geom),
                    ST_Distance(sep.end_geom, tb.geom)
                )) as min_distance
            FROM bdtopo.trains_buffer tb, start_end_points sep
            GROUP BY tb.nature
            ORDER BY min_distance
            LIMIT 1
        )
        SELECT 
            COALESCE(SUM(ST_Distance(geom1, geom2) / 1000.0), 0) as consecutive_train_length,
            (SELECT COALESCE(SUM(ST_Distance(geom1, geom2) / 1000.0), 0) FROM all_train_segments) as total_train_length,
            (SELECT COALESCE(MIN(ST_Distance(start_geom, tb.geom)), 999999) FROM bdtopo.trains_buffer tb, start_end_points) as start_distance,
            (SELECT COALESCE(MIN(ST_Distance(end_geom, tb.geom)), 999999) FROM bdtopo.trains_buffer tb, start_end_points) as end_distance,
            (SELECT segment_nature FROM most_common_intersecting_nature) as intersecting_nature,
            (SELECT nature FROM nearest_start_end_nature WHERE min_distance < %s) as start_end_nature
        FROM consecutive_in_train_segments
    ', schema_name, distance_to_train);
    
    EXECUTE sql_query INTO train_length, total_train_length, start_point_distance, end_point_distance, intersecting_nature, start_end_nature USING trip_id;
    
    -- Log the calculated values
    RAISE NOTICE 'Schema: %, Trip ID: %, Total Distance: % km, Avg Speed: % km/h, Train Length (consecutive): % km, Total Train Length (all): % km, Start Point Distance to Train: % m, End Point Distance to Train: % m, Intersecting Nature: %, Start/End Nature: %, Min Train Ratio: %, Min Metro Length Ratio: %, Min Train Distance: % km, Min Train Speed: % km/h, Distance to Train: % m', 
        schema_name, trip_id, total_distance, avg_speed, train_length, total_train_length, start_point_distance, end_point_distance, intersecting_nature, start_end_nature, min_train_ratio, min_metro_length_ratio, min_train_distance, min_train_speed, distance_to_train;
    
    -- Apply logic based on consecutive train_length ratio
    IF train_length > (min_train_ratio * total_distance) THEN
        -- High train coverage: check minimum distance and average speed, return intersecting nature
        IF (total_distance > min_train_distance) AND (avg_speed > min_train_speed) AND intersecting_nature IS NOT NULL THEN
            RETURN intersecting_nature;
        ELSE
            RETURN 'NOT_TRAIN';
        END IF;
               
    ELSIF train_length < (min_train_ratio * total_distance) AND train_length > (min_metro_length_ratio * total_distance) THEN
        -- Medium train coverage: check start/end points proximity to train buffer AND average speed
        IF (start_point_distance < distance_to_train AND end_point_distance < distance_to_train AND avg_speed > min_train_speed AND total_distance > min_train_distance) THEN
            -- Return the nature of the train buffer closest to start/end points
            IF start_end_nature IS NOT NULL THEN
                RETURN start_end_nature;
            ELSE
                RETURN 'NOT_TRAIN';
            END IF;
        ELSE
            RETURN 'NOT_TRAIN';
        END IF;
        
    ELSE
        -- Low train coverage: return NOT_TRAIN
        RETURN 'NOT_TRAIN';
    END IF;
END;
$BODY$;