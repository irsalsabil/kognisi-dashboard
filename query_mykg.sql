SELECT *
FROM (
    SELECT 
        u.email, 
        u.name,
        u.nik,
        CONCAT(cp.title, '-', COALESCE(cs.title,''), '-', COALESCE(cm.title,'')) AS 'title', 
        cmu.updated_at AS 'last_updated',
        cmu.progress_duration AS 'duration',
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
    
    UNION ALL
    
    SELECT DISTINCT
        u.email, 
        u.name, 
        u.nik,
        CONCAT(c.title, '-', COALESCE(cs.name, ''), '-', COALESCE(cs2.name, '')) AS 'title',
        cu.updated_at AS 'last_updated',
        CASE 
			WHEN c.type = 1 THEN cu.progress_duration
			WHEN c.type = 2 THEN TIME_TO_SEC(TIMEDIFF(cs2.end_time, cs2.start_time)) 
		END AS duration,
        CASE WHEN c.type = 1 THEN 'Video'
            WHEN c.type = 2 THEN 'Inclass' END AS 'type',
        'Kognisi MyKG' AS 'platform'
    FROM course_users cu
        JOIN users u ON cu.user_id = u.id 
        JOIN courses c ON cu.course_id = c.id
        LEFT JOIN course_schedules cs ON cs.course_id = c.id 
		LEFT JOIN course_sessions cs2 ON cs2.course_schedule_id = cs.id 
        LEFT JOIN course_instructors ci ON c.id = ci.course_id
    WHERE 
        u.name NOT IN ('SISDMv2','SEMOGA LAST TEST','Testing aja','TEST')
        AND ci.deleted_at IS NULL
        AND c.deleted_at IS NULL
) AS combined_results
ORDER BY
	last_updated DESC