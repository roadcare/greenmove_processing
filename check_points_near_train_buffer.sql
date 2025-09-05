CREATE OR REPLACE FUNCTION check_points_near_train_buffer(
    longitude1 DOUBLE PRECISION,
    latitude1 DOUBLE PRECISION,
    longitude2 DOUBLE PRECISION,
    latitude2 DOUBLE PRECISION,
    max_distrain DOUBLE PRECISION DEFAULT 100.0
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    point1_geom GEOMETRY;
    point2_geom GEOMETRY;
    point1_near_train BOOLEAN DEFAULT FALSE;
    point2_near_train BOOLEAN DEFAULT FALSE;
BEGIN
    -- Create point geometries from input coordinates (WGS84 - EPSG:4326)
    point1_geom := ST_SetSRID(ST_Point(longitude1, latitude1), 4326);
    point2_geom := ST_SetSRID(ST_Point(longitude2, latitude2), 4326);
    
    -- Transform points to Lambert 93 (EPSG:2154) to match train_buffer geometry
    point1_geom := ST_Transform(point1_geom, 2154);
    point2_geom := ST_Transform(point2_geom, 2154);
    
    -- Check if point1 is within max_distrain distance from any train buffer
    SELECT EXISTS (
        SELECT 1 
        FROM bdtopo.train_buffer 
        WHERE ST_DWithin(geom, point1_geom, max_distrain)
    ) INTO point1_near_train;
    
    -- Check if point2 is within max_distrain distance from any train buffer
    SELECT EXISTS (
        SELECT 1 
        FROM bdtopo.train_buffer 
        WHERE ST_DWithin(geom, point2_geom, max_distrain)
    ) INTO point2_near_train;
    
    -- Return TRUE only if BOTH points are near train lines
    RETURN point1_near_train AND point2_near_train;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Return FALSE in case of any error (invalid coordinates, etc.)
        RETURN FALSE;
END;
$$;