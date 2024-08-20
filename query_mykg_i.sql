SELECT 
        '-' AS 'email',
        i.name,
        i.nik,
        c.title,
        c.created_at AS 'last_updated',
        SUM(CASE 
            WHEN c.type = 1 THEN a.duration 
            WHEN c.type = 2 THEN TIME_TO_SEC(TIMEDIFF(cs2.end_time, cs2.start_time)) 
        END) AS duration,  -- Sum up the duration
        CASE WHEN c.type = 1 THEN 'Video'
            WHEN c.type = 2 THEN 'Inclass' END AS 'type',
        'Kognisi MyKG' AS 'platform'
FROM
		course_instructors ci 
LEFT JOIN
		instructors i ON instructor_id = i.id
LEFT JOIN
		courses c ON ci.course_id = c.id 
LEFT JOIN 
		attachments a ON a.id = c.attachment_id
LEFT JOIN 
	course_schedules cs ON cs.course_id = c.id 
LEFT JOIN 
	course_sessions cs2 ON cs2.course_schedule_id = cs.id
WHERE 
        ci.deleted_at IS NULL
        AND c.deleted_at IS NULL
GROUP BY i.name, i.nik, c.title, c.type, c.created_at 