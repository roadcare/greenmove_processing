-- OPTIMIZATION 3: Alternative approach using materialized spatial joins
CREATE OR REPLACE FUNCTION public.detect_train_trip_type_sig_schema_dev_fast(
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
    result_record RECORD;
    sql_query TEXT;
BEGIN
    sql_query := format('
        WITH trip_metadata AS (
            SELECT "totalDistance", "avgSpeed"
            FROM %I.trip 
            WHERE id = $1
        ),
        trip_line AS (
            SELECT ST_MakeLine(
                ST_Transform(ST_SetSRID(ST_MakePoint(long, lat), 4326), 2154) 
                ORDER BY timestamp
            ) as geom
            FROM %I."tripDetail"
            WHERE "tripId" = $1 AND "isValid" = true
        ),
        intersecting_trains AS (
            SELECT 
                tb.nature,
                ST_Length(ST_Intersection(tl.geom, tb.geom)) / 1000.0 as intersection_length
            FROM trip_line tl
            CROSS JOIN bdtopo.trains_buffer tb
            WHERE ST_Intersects(tl.geom, tb.geom)
        ),
        trip_endpoints AS (
            SELECT 
                ST_StartPoint(geom) as start_point,
                ST_EndPoint(geom) as end_point
            FROM trip_line
        )
        SELECT 
            tm."totalDistance",
            tm."avgSpeed",
            COALESCE(MAX(it.intersection_length), 0) as max_intersection,
            (
                SELECT nature 
                FROM intersecting_trains 
                ORDER BY intersection_length DESC 
                LIMIT 1
            ) as dominant_nature,
            (
                SELECT tb.nature
                FROM bdtopo.trains_buffer tb, trip_endpoints te
                ORDER BY LEAST(
                    ST_Distance(te.start_point, tb.geom),
                    ST_Distance(te.end_point, tb.geom)
                )
                LIMIT 1
            ) as closest_nature,
            (
                SELECT MIN(LEAST(
                    ST_Distance(te.start_point, tb.geom),
                    ST_Distance(te.end_point, tb.geom)
                ))
                FROM bdtopo.trains_buffer tb, trip_endpoints te
            ) as min_endpoint_distance
        FROM trip_metadata tm
        CROSS JOIN trip_line tl
        LEFT JOIN intersecting_trains it ON true
        CROSS JOIN trip_endpoints te
        GROUP BY tm."totalDistance", tm."avgSpeed"
    ', schema_name, schema_name);
    
    EXECUTE sql_query INTO result_record USING trip_id;
    
    -- Quick validation and decision
    IF result_record."totalDistance" IS NULL 
       OR result_record."avgSpeed" IS NULL 
       OR result_record."totalDistance" <= min_train_distance 
       OR result_record."avgSpeed" <= min_train_speed THEN
        RETURN 'NOT_TRAIN';
    END IF;
    
    -- Decision logic based on intersection ratio
    IF result_record.max_intersection > (min_train_ratio * result_record."totalDistance") THEN
        RETURN COALESCE(result_record.dominant_nature, 'NOT_TRAIN');
    ELSIF result_record.max_intersection > (min_metro_length_ratio * result_record."totalDistance") 
          AND result_record.min_endpoint_distance < distance_to_train THEN
        RETURN COALESCE(result_record.closest_nature, 'NOT_TRAIN');
    ELSE
        RETURN 'NOT_TRAIN';
    END IF;
END;
$BODY$;