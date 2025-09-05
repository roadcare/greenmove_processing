CREATE OR REPLACE FUNCTION calculate_trip_point_density(trip_id_param UUID)
RETURNS DECIMAL(10,4)
AS $$
DECLARE
    valid_points_count INTEGER;
    total_distance DECIMAL;
    density DECIMAL(10,4);
BEGIN
    -- Get count of valid tripDetail points for the specified trip
    SELECT COUNT(*)
    INTO valid_points_count
    FROM public."tripDetail"
    WHERE tripId = trip_id_param AND "isValid" = true;
    
    -- Get total distance from trip table
    SELECT "totalDistance"
    INTO total_distance
    FROM public.trip
    WHERE id = trip_id_param;
    
    -- Handle edge cases and calculate density (points per kilometer)
    IF total_distance IS NULL OR total_distance <= 0 THEN
        -- Return NULL for invalid or zero distance trips
        RETURN NULL;
    ELSE
        -- Calculate density as valid points per kilometer
        density := valid_points_count::DECIMAL / total_distance;
        RETURN density;
    END IF;
    
EXCEPTION
    -- Handle case where trip doesn't exist
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
    WHEN OTHERS THEN
        -- Log error and return NULL
        RAISE NOTICE 'Error calculating density for trip %: %', trip_id_param, SQLERRM;
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Usage example:
-- SELECT calculate_trip_point_density(123);

-- To get density for all trips:
-- SELECT 
--     t.id,
--     t.vehicle,
--     t."totalDistance",
--     calculate_trip_point_density(t.id) as point_density_per_km
-- FROM public.trip t
-- ORDER BY t.id;