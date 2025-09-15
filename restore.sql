DO $$
BEGIN
    INSERT INTO public."tripDetail"
    SELECT *
    FROM  restore0409."tripDetail" s
    WHERE NOT EXISTS (
        SELECT 1
        FROM public."tripDetail" d
        WHERE d.id = s.id
    );
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error occurred: %', SQLERRM;
END $$;