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
    start_point_distance REAL;
    end_point_distance REAL;
    train_length REAL := 0;
    intersecting_nature TEXT;
    start_end_nature TEXT;
    sql_query TEXT;
    trip_bbox GEOMETRY;
BEGIN
    -- Early validation - get trip metadata first
    sql_query := format('SELECT "totalDistance", "avgSpeed" FROM %I.trip WHERE id = $1', schema_name);
    EXECUTE sql_query INTO total_distance, avg_speed USING trip_id;
    
    -- Early exit conditions
    IF total_distance IS NULL OR avg_speed IS NULL THEN
        RETURN 'NOT_TRAIN';
    END IF;
    
    IF total_distance <= min_train_distance OR avg_speed <= min_train_speed THEN
        RETURN 'NOT_TRAIN';
    END IF;
    
    -- OPTIMIZATION: Check start/end point distances first for early exit
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
        )
        SELECT 
            (SELECT MIN(ST_Distance(start_geom, tb.geom)) FROM bdtopo.trains_buffer tb) as start_distance,
            (SELECT MIN(ST_Distance(end_geom, tb.geom)) FROM bdtopo.trains_buffer tb) as end_distance
        FROM trip_endpoints
    ', schema_name, schema_name, schema_name, schema_name);
    
    EXECUTE sql_query INTO start_point_distance, end_point_distance USING trip_id;
    
    -- Early exit: if both start and end points are far from train infrastructure
    IF start_point_distance > distance_to_train AND end_point_distance > distance_to_train THEN
        RAISE NOTICE 'Early exit: Start distance: % m, End distance: % m, Threshold: % m', 
            start_point_distance, end_point_distance, distance_to_train;
        RETURN 'NOT_TRAIN';
    END IF;
    
    -- Continue with full analysis only if start/end check passed
    -- Get trip bounding box for spatial filtering
    sql_query := format('
        SELECT ST_Envelope(ST_Collect(ST_Transform(ST_SetSRID(ST_MakePoint(long, lat), 4326), 2154)))
        FROM %I."tripDetail" 
        WHERE "tripId" = $1 AND "isValid" = true
    ', schema_name);
    EXECUTE sql_query INTO trip_bbox USING trip_id;
    
    IF trip_bbox IS NULL THEN
        RETURN 'NOT_TRAIN';
    END IF;
    
    -- Optimized main query with spatial pre-filtering
    sql_query := format('
        WITH trip_points AS (
            SELECT 
                td.timestamp,
                ST_Transform(ST_SetSRID(ST_MakePoint(td.long, td.lat), 4326), 2154) as geom,
                ROW_NUMBER() OVER (ORDER BY td.timestamp) as rn
            FROM %I."tripDetail" td
            WHERE td."tripId" = $1 AND td."isValid" = true
            ORDER BY td.timestamp
        ),
        -- Pre-filter train buffers using bounding box (major performance gain)
        relevant_trains AS (
            SELECT id, nature, geom
            FROM bdtopo.trains_buffer tb
            WHERE ST_Intersects(tb.geom, $2)
        ),
        point_train_intersections AS (
            SELECT 
                tp.rn,
                tp.geom,
                rt.nature,
                CASE WHEN ST_Within(tp.geom, rt.geom) THEN 1 ELSE 0 END as is_in_train
            FROM trip_points tp
            LEFT JOIN relevant_trains rt ON ST_Within(tp.geom, rt.geom)
        ),
        consecutive_segments AS (
            SELECT 
                p1.geom as geom1,
                p2.geom as geom2,
                p1.nature as segment_nature,
                ST_Distance(p1.geom, p2.geom) / 1000.0 as segment_distance
            FROM point_train_intersections p1
            JOIN point_train_intersections p2 ON p2.rn = p1.rn + 1
            WHERE p1.is_in_train = 1 AND p2.is_in_train = 1
        ),
        start_end_analysis AS (
            SELECT 
                (SELECT geom FROM trip_points WHERE rn = 1) as start_geom,
                (SELECT geom FROM trip_points WHERE rn = (SELECT MAX(rn) FROM trip_points)) as end_geom
        )
        SELECT 
            COALESCE(SUM(cs.segment_distance), 0) as consecutive_train_length,
            -- Most frequent nature among consecutive segments
            (
                SELECT segment_nature 
                FROM consecutive_segments 
                WHERE segment_nature IS NOT NULL
                GROUP BY segment_nature 
                ORDER BY SUM(segment_distance) DESC, segment_nature 
                LIMIT 1
            ) as most_common_nature,
            -- Closest nature to start/end points (only if within threshold)
            (
                SELECT rt.nature
                FROM relevant_trains rt, start_end_analysis sea
                WHERE LEAST(
                    ST_Distance(sea.start_geom, rt.geom),
                    ST_Distance(sea.end_geom, rt.geom)
                ) < $3
                ORDER BY LEAST(
                    ST_Distance(sea.start_geom, rt.geom),
                    ST_Distance(sea.end_geom, rt.geom)
                )
                LIMIT 1
            ) as closest_nature
        FROM consecutive_segments cs
    ', schema_name);
    
    EXECUTE sql_query INTO train_length, intersecting_nature, start_end_nature 
    USING trip_id, trip_bbox, distance_to_train;
    
    -- Log the calculated values (including early distance check results)
    RAISE NOTICE 'Schema: %, Trip ID: %, Total Distance: % km, Avg Speed: % km/h, Train Length (consecutive): % km, Start Point Distance: % m, End Point Distance: % m, Intersecting Nature: %, Start/End Nature: %, Distance to Train Threshold: % m', 
        schema_name, trip_id, total_distance, avg_speed, train_length, start_point_distance, end_point_distance, intersecting_nature, start_end_nature, distance_to_train;
    
    -- Simplified decision logic
    IF train_length > (min_train_ratio * total_distance) THEN
        RETURN COALESCE(intersecting_nature, 'NOT_TRAIN');
    ELSIF train_length > (min_metro_length_ratio * total_distance) THEN
        RETURN COALESCE(start_end_nature, 'NOT_TRAIN');
    ELSE
        RETURN 'NOT_TRAIN';
    END IF;
END;
$BODY$;