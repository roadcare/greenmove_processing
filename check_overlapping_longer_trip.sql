CREATE OR REPLACE FUNCTION public.check_overlapping_longer_trip_dev(
    trip_id uuid)
    RETURNS boolean
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    input_user_id UUID;
    input_start_time TIMESTAMP;
    input_end_time TIMESTAMP;
    input_duration INTERVAL;
    overlapping_count INTEGER;
    overlapping_trip_record RECORD;
BEGIN
    -- Get details of the input trip
    SELECT 
        "userId",
        "startTime",
        "endTime",
        ("endTime" - "startTime") as duration
    INTO 
        input_user_id,
        input_start_time,
        input_end_time,
        input_duration
    FROM public.trip
    WHERE id = trip_id;
    
    -- If trip not found, return false
    IF input_user_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Check if there exists another trip with the specified conditions
    SELECT COUNT(*)
    INTO overlapping_count
    FROM public.trip t
    WHERE 
        -- Different trip (not the same as input)
        t.id != trip_id
        -- Same user
        AND t."userId" = input_user_id
        -- Trip type is NORMAL
        AND t."tripType" = 'NORMAL'
        -- Time overlap: trip intervals overlap if startTime < other_endTime AND endTime > other_startTime
        AND input_start_time < t."endTime"
        AND input_end_time - t."startTime" > INTERVAL '1 minute'
        -- Longer duration than input trip
        AND (t."endTime" - t."startTime") >= input_duration;
    
    -- If overlapping trips exist, log them
    IF overlapping_count > 0 THEN
        FOR overlapping_trip_record IN
            SELECT 
                t.id,
                t."startTime",
                t."endTime",
                (t."endTime" - t."startTime") as duration
            FROM public.trip t
            WHERE 
                t.id != trip_id
                AND t."userId" = input_user_id
                AND t."tripType" = 'NORMAL'
                AND input_start_time < t."endTime"
                AND input_end_time - t."startTime" > INTERVAL '1 minute'
                AND (t."endTime" - t."startTime") >= input_duration
        LOOP
            RAISE NOTICE 'Trip % overlaps with trip % (duration: %, start: %, end: %)',
                trip_id,
                overlapping_trip_record.id,
                overlapping_trip_record.duration,
                overlapping_trip_record."startTime",
                overlapping_trip_record."endTime";
        END LOOP;
    END IF;
    
    -- Return true if at least one such trip exists
    RETURN overlapping_count > 0;
END;
$BODY$;