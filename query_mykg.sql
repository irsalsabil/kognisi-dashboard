SELECT *
FROM (
    SELECT 
        u.email, 
        u.name,
        u.nik,
        CONCAT(cp.title, '-', cs.title, '-', cm.title) AS 'title', 
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
    
    UNION ALL
    
    SELECT DISTINCT
        u.email, 
        u.name, 
        u.nik,
        c.title,
        cu.updated_at AS 'last_updated', 
        cu.progress_duration AS 'duration', 
        CASE WHEN c.type = 1 THEN 'Video'
            WHEN c.type = 2 THEN 'Inclass' END AS 'type',
        'Kognisi MyKG' AS 'platform'
    FROM course_users cu
        JOIN users u ON cu.user_id = u.id 
        JOIN courses c ON cu.course_id = c.id
        LEFT JOIN course_instructors ci ON c.id = ci.course_id
        LEFT JOIN instructors i ON ci.instructor_id = i.id
    WHERE 
        u.name NOT IN ('SISDMv2','SEMOGA LAST TEST','Testing aja','TEST')
        AND ci.deleted_at IS NULL 
) AS combined_results
ORDER BY
	last_updated DESC