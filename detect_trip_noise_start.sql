CREATE OR REPLACE FUNCTION detect_trip_noise_start_dev(
    trip_id UUID,
    noise_threshold FLOAT DEFAULT 0.50,  -- 50% by default
    min_speed_threshold FLOAT DEFAULT 1.5  -- 1 km/h by default (very slow movement considered noise)
)
RETURNS TABLE(
    noise_start_timestamp TIMESTAMP,
    total_points_from_start INTEGER,
    noise_points_from_start INTEGER,
    noise_percentage_from_start FLOAT,
    trip_start_timestamp TIMESTAMP,
    trip_end_timestamp TIMESTAMP
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH trip_points AS (
        SELECT 
            "tripId",
            timestamp,
            lat,
            long,
            accuracy,
            vehicle,
            "isValid",
            heading,
            -- Calculate distance from previous point
            LAG(lat) OVER (ORDER BY timestamp) AS prev_lat,
            LAG(long) OVER (ORDER BY timestamp) AS prev_long,
            LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp,
            LAG(heading) OVER (ORDER BY timestamp) AS prev_heading,
            -- Calculate distance to next point  
            LEAD(lat) OVER (ORDER BY timestamp) AS next_lat,
            LEAD(long) OVER (ORDER BY timestamp) AS next_long,
            LEAD(timestamp) OVER (ORDER BY timestamp) AS next_timestamp
        FROM public."tripDetail"
        WHERE "tripId" = trip_id
        ORDER BY timestamp
    ),
    
    noise_analysis AS (
        SELECT *,
            -- Distance from previous point (Haversine formula in meters)
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
            
            -- Time difference from previous point (seconds)
            CASE 
                WHEN prev_timestamp IS NOT NULL THEN
                    EXTRACT(EPOCH FROM (timestamp - prev_timestamp))
                ELSE 0
            END AS time_diff_prev,
            
            -- Speed calculation (m/s)
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
            
            -- Heading change from previous point
            CASE 
                WHEN prev_heading IS NOT NULL AND heading != -1 AND prev_heading != -1 THEN
                    LEAST(
                        ABS(heading - prev_heading),
                        360 - ABS(heading - prev_heading)
                    )
                ELSE 0
            END AS heading_change,
            
            -- Vector angle calculation (angle between current->prev and current->next)
            CASE 
                WHEN prev_lat IS NOT NULL AND next_lat IS NOT NULL THEN
                    -- Calculate angle between current->prev and current->next vectors
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
            -- Detect various types of noise (same logic as detect_gps_noise_zones)
            CASE
                WHEN NOT "isValid" THEN true
                WHEN accuracy > 50 THEN true  -- Poor GPS accuracy
                WHEN heading_change > 90 THEN true  -- Sudden heading change
                WHEN calculated_speed > 50 AND distance_from_prev < 10 THEN true  -- Impossible speed with small distance
                WHEN time_diff_prev > 0 AND time_diff_prev < 10 AND distance_from_prev > 100 THEN true  -- GPS jump
                WHEN vector_angle IS NOT NULL AND ABS(vector_angle) < 15 THEN true  -- Small vector angle (back and forth)
                WHEN distance_from_prev < 2 AND time_diff_prev > 30 THEN true  -- Too close points with long time gap
                WHEN calculated_speed < (min_speed_threshold / 3.6) THEN true  -- Very slow movement (convert km/h to m/s)
                ELSE false
            END AS is_noise
        FROM noise_analysis
    ),
    
    running_totals AS (
        SELECT *,
            -- Calculate running totals from current point to end of trip (reverse order)
            COUNT(*) OVER (ORDER BY timestamp DESC ROWS UNBOUNDED PRECEDING) AS points_to_end,
            SUM(CASE WHEN is_noise THEN 1 ELSE 0 END) OVER (ORDER BY timestamp DESC ROWS UNBOUNDED PRECEDING) AS noise_points_to_end,
            MIN(timestamp) OVER () AS trip_start_time,
            MAX(timestamp) OVER () AS trip_end_time
        FROM noise_detection
    ),
    
    noise_percentages AS (
        SELECT *,
            -- Calculate noise percentage from current point to end
            CASE 
                WHEN points_to_end > 0 THEN 
                    noise_points_to_end::FLOAT / points_to_end::FLOAT
                ELSE 0
            END AS noise_percentage_to_end
        FROM running_totals
    ),
    
    threshold_candidates AS (
        SELECT 
            timestamp,
            points_to_end,
            noise_points_to_end,
            noise_percentage_to_end,
            trip_start_time,
            trip_end_time
        FROM noise_percentages
        WHERE noise_percentage_to_end >= noise_threshold
        ORDER BY timestamp ASC
        LIMIT 1  -- Get the earliest timestamp that meets the criteria
    ),
    
    refined_noise_start AS (
        SELECT 
            tc.*,
            -- Find the first actual noise point from the threshold timestamp forward
            (SELECT nd.timestamp 
             FROM noise_detection nd 
             WHERE nd.timestamp >= tc.timestamp 
               AND nd.is_noise = true
             ORDER BY nd.timestamp ASC 
             LIMIT 1) AS actual_first_noise_timestamp
        FROM threshold_candidates tc
    )
    
    SELECT 
        COALESCE(rns.actual_first_noise_timestamp, rns.timestamp) AS noise_start_timestamp,
        -- Recalculate counts from the actual first noise timestamp
        (SELECT COUNT(*)::INTEGER 
         FROM noise_detection nd2 
         WHERE nd2.timestamp >= COALESCE(rns.actual_first_noise_timestamp, rns.timestamp)) AS total_points_from_start,
        (SELECT COUNT(*)::INTEGER 
         FROM noise_detection nd3 
         WHERE nd3.timestamp >= COALESCE(rns.actual_first_noise_timestamp, rns.timestamp) 
           AND nd3.is_noise = true) AS noise_points_from_start,
        -- Recalculate percentage from the actual first noise timestamp  
        CASE 
            WHEN (SELECT COUNT(*) FROM noise_detection nd4 WHERE nd4.timestamp >= COALESCE(rns.actual_first_noise_timestamp, rns.timestamp)) > 0 THEN
                (SELECT COUNT(*)::FLOAT FROM noise_detection nd5 WHERE nd5.timestamp >= COALESCE(rns.actual_first_noise_timestamp, rns.timestamp) AND nd5.is_noise = true) /
                (SELECT COUNT(*)::FLOAT FROM noise_detection nd6 WHERE nd6.timestamp >= COALESCE(rns.actual_first_noise_timestamp, rns.timestamp))
            ELSE 0
        END AS noise_percentage_from_start,
        rns.trip_start_time AS trip_start_timestamp,
        rns.trip_end_time AS trip_end_timestamp
    FROM refined_noise_start rns;
END;
$$;

-- Example usage:
-- SELECT * FROM detect_trip_noise_start('your-trip-uuid-here', 0.55, 5);    -- 55% threshold, 5 km/h speed limit
-- SELECT * FROM detect_trip_noise_start('your-trip-uuid-here', 0.3, 2);     -- 30% threshold, 2 km/h speed limit  
-- SELECT * FROM detect_trip_noise_start('your-trip-uuid-here');             -- Default 55% threshold, 5 km/h speed limit

COMMENT ON FUNCTION detect_trip_noise_start_dev(UUID, FLOAT, FLOAT) IS 
'Detects the earliest timestamp in a trip where the noise percentage from that point to the end of the trip exceeds the specified threshold (default 55%). Includes detection of very slow movement below min_speed_threshold (default 5 km/h) as noise. Useful for identifying when GPS noise starts becoming prevalent at the end of trips (e.g., when entering buildings).';