SELECT  
    u.email, 
    u.name, 
    '000000' AS 'nik',
    CASE 
        WHEN ubr.bundle_id = 1 THEN 'GI'
        WHEN ubr.bundle_id = 2 THEN 'LEAN'
        WHEN ubr.bundle_id = 3 THEN 'ELITE'
        WHEN ubr.bundle_id = 4 THEN 'Genuine'
        WHEN ubr.bundle_id = 5 THEN 'Astaka'
    END AS 'title',
    ubr.created_at AS 'last_updated',
    1200 AS 'duration', 
    'Assessment' AS 'type',
    'Discovery' AS 'platform'
FROM 
    user_bundle_results ubr 
LEFT JOIN
    users u ON u.id = ubr.user_id
   ORDER BY
ubr.created_at DESC