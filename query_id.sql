SELECT 
	u.email, 
	u.full_name AS 'name', 
	'-' AS 'nik',
	CONCAT (c.title, '-', COALESCE(cs.title, ''), '-', COALESCE(cc.title, '')) AS 'title', 
	cup.updated_at AS 'last_updated',
	ROUND (cup.progress_duration, 0) AS 'duration',
	'Course' AS 'type', 
	'Kognisi.id' AS 'platform'
FROM 
	course_user_progress cup 
LEFT JOIN
	course_users cu ON cup.course_serial = cu.course_serial 
		AND cup.user_serial = cu.user_serial 
LEFT JOIN 
	course_contents cc ON cup.course_content_serial = cc.serial
LEFT JOIN 
	course_sections cs ON cup.course_section_serial = cs.serial
LEFT JOIN 
	courses c ON cup.course_serial = c.serial
LEFT JOIN 
	categories cat ON c.category_serial = cat.serial  
LEFT JOIN 
	users u ON cup.user_serial = u.serial
WHERE 
	cc.type = 'VIDEO'
	AND u.id IS NOT NULL