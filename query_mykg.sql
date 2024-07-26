SELECT *
FROM (
    -- First part: Aggregating duration and using only cp.title
    SELECT 
        u.email, 
        u.name,
        u.nik,
        cp.title AS 'title',  -- Use only cp.title
        MAX(cmu.updated_at) AS 'last_updated',  -- Get the latest update date
        SUM(cmu.progress_duration) AS 'duration',  -- Sum up the duration
        'Course' AS 'type', 
        'Kognisi MyKG' AS 'platform'
    FROM course_material_users cmu
        LEFT JOIN course_package_user_enrollments cpue ON
            cpue.user_id = cmu.user_id
            AND cmu.course_package_id = cpue.course_package_id
        JOIN users u ON
            u.id = cmu.user_id
        JOIN course_materials cm ON
            cmu.course_material_id = cm.id 
        JOIN course_sections cs ON
            cmu.course_section_id = cs.id 
        JOIN course_packages cp ON
            cmu.course_package_id = cp.id
    WHERE 
        u.name NOT IN ('SISDMv2','SEMOGA LAST TEST','Testing aja','TEST')
        AND cm.deleted_at IS NULL
        AND cp.title NOT IN ('Kursus Contoh')
    GROUP BY u.email, u.name, u.nik, cp.title  -- Group by necessary fields

    UNION ALL
    
    -- Second part: Using only c.title and summing up the duration
    SELECT 
        u.email, 
        u.name, 
        u.nik,
        c.title AS 'title',  -- Use only c.title
        MAX(cu.updated_at) AS 'last_updated',
        SUM(CASE 
            WHEN c.type = 1 THEN cu.progress_duration
            WHEN c.type = 2 THEN TIME_TO_SEC(TIMEDIFF(cs2.end_time, cs2.start_time)) 
        END) AS duration,  -- Sum up the duration
        CASE WHEN c.type = 1 THEN 'Video'
            WHEN c.type = 2 THEN 'Inclass' END AS 'type',
        'Kognisi MyKG' AS 'platform'
    FROM course_users cu
        JOIN users u ON cu.user_id = u.id 
        JOIN courses c ON cu.course_id = c.id
        LEFT JOIN course_schedules cs ON cs.course_id = c.id 
        LEFT JOIN course_sessions cs2 ON cs2.course_schedule_id = cs.id 
        LEFT JOIN course_instructors ci ON c.id = ci.course_id AND cs2.id = ci.course_session_id 
    WHERE 
        u.name NOT IN ('SISDMv2','SEMOGA LAST TEST','Testing aja','TEST')
        AND ci.deleted_at IS NULL
        AND c.deleted_at IS NULL
    GROUP BY u.email, u.name, u.nik, c.title, c.type  -- Group by necessary fields
) AS combined_results
ORDER BY
    last_updated DESC