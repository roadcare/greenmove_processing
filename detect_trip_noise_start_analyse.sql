CREATE OR REPLACE FUNCTION detect_trip_noise_start_analyse(
    trip_id UUID,
    noise_threshold FLOAT DEFAULT 0.5,  -- 50% by default
    min_speed_threshold FLOAT DEFAULT 1.5  -- 1.5 km/h by default (very slow movement considered noise)
)
RETURNS TABLE(
    times_tamp TIMESTAMP,
    noise_types TEXT[],
    is_noise BOOLEAN,
    calculated_speed FLOAT,
    distance_from_prev FLOAT,
    heading_change FLOAT,
    accuracy FLOAT,
    vector_angle FLOAT,
    time_diff_prev FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH trip_points AS (
        SELECT 
            "tripId",
            td."timestamp",
            lat,
            long,
            td.accuracy,
            vehicle,
            "isValid",
            heading,
            LAG(lat) OVER (ORDER BY td."timestamp") AS prev_lat,
            LAG(long) OVER (ORDER BY td."timestamp") AS prev_long,
            LAG(td."timestamp") OVER (ORDER BY td."timestamp") AS prev_timestamp,
            LAG(heading) OVER (ORDER BY td."timestamp") AS prev_heading,
            LEAD(lat) OVER (ORDER BY td."timestamp") AS next_lat,
            LEAD(long) OVER (ORDER BY td."timestamp") AS next_long,
            LEAD(td."timestamp") OVER (ORDER BY td."timestamp") AS next_timestamp
        FROM public."tripDetail" td
        WHERE "tripId" = trip_id
        ORDER BY td."timestamp"
    ),
    noise_analysis AS (
        SELECT *,
            CASE 
                WHEN prev_lat IS NOT NULL AND prev_long IS NOT NULL THEN
                    6371000 * acos(
                        GREATEST(-1, LEAST(1, 
                            cos(radians(prev_lat)) * cos(radians(lat)) * 
                            cos(radians(long) - radians(prev_long)) + 
                            sin(radians(prev_lat)) * sin(radians(lat))
                        ))
                    )
                ELSE 0
            END AS distance_from_prev,
            CASE 
                WHEN prev_timestamp IS NOT NULL THEN
                    EXTRACT(EPOCH FROM (timestamp - prev_timestamp))
                ELSE 0
            END AS time_diff_prev,
            CASE 
                WHEN prev_timestamp IS NOT NULL AND 
                     EXTRACT(EPOCH FROM (timestamp - prev_timestamp)) > 0 THEN
                    (6371000 * acos(
                        GREATEST(-1, LEAST(1,
                            cos(radians(prev_lat)) * cos(radians(lat)) * 
                            cos(radians(long) - radians(prev_long)) + 
                            sin(radians(prev_lat)) * sin(radians(lat))
                        ))
                    )) / EXTRACT(EPOCH FROM (timestamp - prev_timestamp))
                ELSE 0
            END AS calculated_speed,
            CASE 
                WHEN prev_heading IS NOT NULL AND heading != -1 AND prev_heading != -1 THEN
                    LEAST(
                        ABS(heading - prev_heading),
                        360 - ABS(heading - prev_heading)
                    )
                ELSE 0
            END AS heading_change,
            CASE 
                WHEN prev_lat IS NOT NULL AND next_lat IS NOT NULL THEN
                    DEGREES(
                        ATAN2(
                            SIN(RADIANS(next_long - long)) * COS(RADIANS(next_lat)),
                            COS(RADIANS(lat)) * SIN(RADIANS(next_lat)) - 
                            SIN(RADIANS(lat)) * COS(RADIANS(next_lat)) * COS(RADIANS(next_long - long))
                        ) -
                        ATAN2(
                            SIN(RADIANS(prev_long - long)) * COS(RADIANS(prev_lat)),
                            COS(RADIANS(lat)) * SIN(RADIANS(prev_lat)) - 
                            SIN(RADIANS(lat)) * COS(RADIANS(prev_lat)) * COS(RADIANS(prev_long - long))
                        )
                    )
                ELSE NULL
            END AS vector_angle
        FROM trip_points
    ),
    noise_detection AS (
        SELECT *,
            -- Build array of detected noise types
            ARRAY_REMOVE(ARRAY[
                CASE WHEN NOT "isValid" THEN 'invalid_point' END,
                CASE WHEN accuracy > 50 THEN 'poor_accuracy' END,
                CASE WHEN heading_change > 90 THEN 'sudden_heading_change' END,
                CASE WHEN calculated_speed > 50 AND distance_from_prev < 10 THEN 'impossible_speed' END,
                CASE WHEN time_diff_prev > 0 AND time_diff_prev < 10 AND distance_from_prev > 100 THEN 'gps_jump' END,
                CASE WHEN vector_angle IS NOT NULL AND ABS(vector_angle) < 15 THEN 'small_vector_angle' END,
                CASE WHEN distance_from_prev < 2 AND time_diff_prev > 30 THEN 'stationary_drift' END,
                CASE WHEN calculated_speed < (min_speed_threshold / 3.6) THEN 'slow_movement' END
            ], NULL) AS detected_noise_types,
            -- Overall noise flag
            CASE
                WHEN NOT "isValid" THEN true
                WHEN accuracy > 50 THEN true
                WHEN heading_change > 90 THEN true
                WHEN calculated_speed > 50 AND distance_from_prev < 10 THEN true
                WHEN time_diff_prev > 0 AND time_diff_prev < 10 AND distance_from_prev > 100 THEN true
                WHEN vector_angle IS NOT NULL AND ABS(vector_angle) < 15 THEN true
                WHEN distance_from_prev < 2 AND time_diff_prev > 30 THEN true
                WHEN calculated_speed < (min_speed_threshold / 3.6) THEN true
                ELSE false
            END AS is_noise_point
        FROM noise_analysis
    ),
    running_totals AS (
        SELECT *,
            COUNT(*) OVER (ORDER BY timestamp DESC ROWS UNBOUNDED PRECEDING) AS points_to_end,
            SUM(CASE WHEN is_noise_point THEN 1 ELSE 0 END) OVER (ORDER BY timestamp DESC ROWS UNBOUNDED PRECEDING) AS noise_points_to_end,
            MIN(timestamp) OVER () AS trip_start_time,
            MAX(timestamp) OVER () AS trip_end_time
        FROM noise_detection
    ),
    noise_percentages AS (
        SELECT *,
            CASE 
                WHEN points_to_end > 0 THEN 
                    noise_points_to_end::FLOAT / points_to_end::FLOAT
                ELSE 0
            END AS noise_percentage_to_end
        FROM running_totals
    ),
    threshold_analysis AS (
        SELECT *,
            -- Check if this point is at or after the noise start threshold
            CASE 
                WHEN noise_percentage_to_end >= noise_threshold THEN true
                ELSE false
            END AS is_in_noise_zone
        FROM noise_percentages
    ),
    trip_noise_start AS (
        SELECT MIN(timestamp) as noise_start_ts
        FROM threshold_analysis
        WHERE is_in_noise_zone = true
    )
    
    SELECT 
        ta."timestamp",
        ta.detected_noise_types AS noise_types,
        ta.is_noise_point AS is_noise,
        ta.calculated_speed,
        ta.distance_from_prev,
        ta.heading_change,
        ta.accuracy,
        ta.vector_angle,
        ta.time_diff_prev
    FROM threshold_analysis ta
    CROSS JOIN trip_noise_start tns
    WHERE ta."timestamp" >= COALESCE(tns.noise_start_ts, ta.trip_end_time)
    ORDER BY ta."timestamp";
END;
$$;

-- Example usage:
-- SELECT * FROM detect_trip_noise_start_analyse('your-trip-uuid-here', 0.5, 1.5);  -- 50% threshold, 1.5 km/h speed limit
-- SELECT * FROM detect_trip_noise_start_analyse('your-trip-uuid-here', 0.3, 2);    -- 30% threshold, 2 km/h speed limit  
-- SELECT * FROM detect_trip_noise_start_analyse('your-trip-uuid-here');            -- Default 50% threshold, 1.5 km/h speed limit
-- 
-- Filter only noise points:
-- SELECT * FROM detect_trip_noise_start_analyse('your-trip-uuid-here') WHERE is_noise = true;
-- 
-- Count noise types:
-- SELECT noise_types, COUNT(*) FROM detect_trip_noise_start_analyse('your-trip-uuid-here') 
-- WHERE array_length(noise_types, 1) > 0 GROUP BY noise_types ORDER BY COUNT(*) DESC;

COMMENT ON FUNCTION detect_trip_noise_start_analyse(UUID, FLOAT, FLOAT) IS 
'Provides detailed analysis of each GPS point from the noise start threshold onwards. Returns "timestamp" (quoted due to reserved keyword), specific noise types detected, and analysis metrics for each point. Uses same thresholds as detect_trip_noise_start (default 50% noise threshold, 1.5 km/h speed limit). Only returns points from the noise start timestamp to trip end.';