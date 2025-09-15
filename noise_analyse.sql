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
        WHERE "tripId" = '6a1be7ab-9d5e-4172-a002-614ce6d29707'::uuid
        ORDER BY td."timestamp"
    )
	
    , noise_analysis AS (
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
    )

	--,noise_detection AS (
        SELECT *,
            -- Build array of detected noise types
            ARRAY_REMOVE(ARRAY[
                CASE wHEN heading = -1 THEN  'invalid_point' END,
                CASE WHEN accuracy > 50 THEN 'poor_accuracy' END,
                CASE WHEN heading_change > 90 THEN 'sudden_heading_change' END,
                CASE WHEN calculated_speed > 50 AND distance_from_prev < 10 THEN 'impossible_speed' END,
                CASE WHEN time_diff_prev > 0 AND time_diff_prev < 10 AND distance_from_prev > 300 THEN 'gps_jump' END,
                CASE WHEN vector_angle IS NOT NULL AND ABS(vector_angle) < 15 THEN 'small_vector_angle' END,
                CASE WHEN distance_from_prev < 2 AND time_diff_prev > 30 THEN 'stationary_drift' END,
                CASE WHEN calculated_speed < (1.5 / 3.6) THEN 'slow_movement' END
            ], NULL) AS detected_noise_types,
            -- Overall noise flag
            CASE
                wHEN heading = -1 THEN true
                WHEN accuracy > 50 THEN true
                WHEN heading_change > 90 THEN true
                WHEN calculated_speed > 50 AND distance_from_prev < 10 THEN true
                WHEN time_diff_prev > 0 AND time_diff_prev < 10 AND distance_from_prev > 100 THEN true
                WHEN vector_angle IS NOT NULL AND ABS(vector_angle) < 15 THEN true
                WHEN distance_from_prev < 2 AND time_diff_prev > 30 THEN true
                WHEN calculated_speed < (1.5 / 3.6) THEN true
                ELSE false
            END AS is_noise_point
        FROM noise_analysis
    --),