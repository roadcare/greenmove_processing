CREATE OR REPLACE FUNCTION public.detect_train_type_dev(
    trip_id uuid,
    schema_name text DEFAULT 'public'::text,
    min_train_distance real DEFAULT 0.5,
    min_train_ratio real DEFAULT 0.5,
    min_metro_length_ratio real DEFAULT 0.18,
    min_train_speed real DEFAULT 15,
    distance_to_train real DEFAULT 150)
    RETURNS text
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    is_train_trip BOOLEAN;
    start_point_distance REAL;
    end_point_distance REAL;
    start_closest_nature TEXT;
    end_closest_nature TEXT;
    sql_query TEXT;
BEGIN
    -- Step 1: Use existing logic to determine if trip is a train trip
    SELECT detect_train_trip_sig_schema_dev(
        trip_id, 
        schema_name, 
        min_train_distance, 
        min_train_ratio, 
        min_metro_length_ratio, 
        min_train_speed, 
        distance_to_train
    ) INTO is_train_trip;
    
    -- Step 2: If not a train trip, return 'NOT_TRAIN'
    IF is_train_trip = FALSE THEN
        RETURN 'NOT_TRAIN';
    END IF;
    
    -- Step 3: If it is a train trip, find closest train_segment to start and end points
    sql_query := format('
        WITH trip_endpoints AS (
            SELECT 
                ST_Transform(ST_SetSRID(ST_MakePoint(
                    (SELECT long FROM %I."tripDetail" WHERE "tripId" = $1 AND "isValid" = true ORDER BY timestamp LIMIT 1),
                    (SELECT lat FROM %I."tripDetail" WHERE "tripId" = $1 AND "isValid" = true ORDER BY timestamp LIMIT 1)
                ), 4326), 2154) as start_geom,
                ST_Transform(ST_SetSRID(ST_MakePoint(
                    (SELECT long FROM %I."tripDetail" WHERE "tripId" = $1 AND "isValid" = true ORDER BY timestamp DESC LIMIT 1),
                    (SELECT lat FROM %I."tripDetail" WHERE "tripId" = $1 AND "isValid" = true ORDER BY timestamp DESC LIMIT 1)
                ), 4326), 2154) as end_geom
        ),
        start_closest AS (
            SELECT 
                ts.nature,
                ST_Distance(te.start_geom, ts.geom) as distance_to_start
            FROM bdtopo.train_segment ts, trip_endpoints te
            ORDER BY ST_Distance(te.start_geom, ts.geom)
            LIMIT 1
        ),
        end_closest AS (
            SELECT 
                ts.nature,
                ST_Distance(te.end_geom, ts.geom) as distance_to_end
            FROM bdtopo.train_segment ts, trip_endpoints te
            ORDER BY ST_Distance(te.end_geom, ts.geom)
            LIMIT 1
        )
        SELECT 
            sc.distance_to_start,
            ec.distance_to_end,
            sc.nature as start_nature,
            ec.nature as end_nature
        FROM start_closest sc, end_closest ec
    ', schema_name, schema_name, schema_name, schema_name);
    
    EXECUTE sql_query INTO start_point_distance, end_point_distance, start_closest_nature, end_closest_nature USING trip_id;
    
    -- Log the calculated values
    RAISE NOTICE 'Trip ID: %, Is Train: %, Start Point Distance: % m, End Point Distance: % m, Start Nature: %, End Nature: %', 
        trip_id, is_train_trip, start_point_distance, end_point_distance, start_closest_nature, end_closest_nature;
    
    -- Step 4: Return nature based on which endpoint is closer to train infrastructure
    IF start_point_distance < end_point_distance THEN
        RETURN COALESCE(start_closest_nature, 'NOT_TRAIN');
    ELSE
        RETURN COALESCE(end_closest_nature, 'NOT_TRAIN');
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error in detect_train_type_dev for trip %: %', trip_id, SQLERRM;
        RETURN 'NOT_TRAIN';
END;
$BODY$;