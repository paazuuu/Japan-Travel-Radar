-- MVP4 demo: two-period social_mentions observations so the 急上昇 (rising)
-- ranking has real growth variance in development. In production these rows are
-- written by the collector over time, not seeded.
-- Re-run safe via NOT EXISTS (the unique index has a NULL source_id, so
-- ON CONFLICT would not fire here).

INSERT INTO observations (entity_type, entity_id, metric, value, observed_at)
SELECT 'spot', s.id, 'social_mentions', v.val, v.obs_date
FROM spots s
JOIN (VALUES
    ('大阪城', 100, (CURRENT_DATE - INTERVAL '7 day')::date), ('大阪城', 180, CURRENT_DATE),
    ('清水寺', 200, (CURRENT_DATE - INTERVAL '7 day')::date), ('清水寺', 240, CURRENT_DATE),
    ('伏見稲荷大社', 150, (CURRENT_DATE - INTERVAL '7 day')::date), ('伏見稲荷大社', 320, CURRENT_DATE),
    ('嵐山 竹林の小径', 120, (CURRENT_DATE - INTERVAL '7 day')::date), ('嵐山 竹林の小径', 130, CURRENT_DATE),
    ('姫路城', 90, (CURRENT_DATE - INTERVAL '7 day')::date), ('姫路城', 200, CURRENT_DATE),
    ('東大寺', 110, (CURRENT_DATE - INTERVAL '7 day')::date), ('東大寺', 115, CURRENT_DATE),
    ('那智の滝', 40, (CURRENT_DATE - INTERVAL '7 day')::date), ('那智の滝', 130, CURRENT_DATE),
    ('高野山 金剛峯寺', 60, (CURRENT_DATE - INTERVAL '7 day')::date), ('高野山 金剛峯寺', 95, CURRENT_DATE),
    ('神戸ハーバーランド', 80, (CURRENT_DATE - INTERVAL '7 day')::date), ('神戸ハーバーランド', 210, CURRENT_DATE),
    ('有馬温泉', 70, (CURRENT_DATE - INTERVAL '7 day')::date), ('有馬温泉', 160, CURRENT_DATE)
) AS v(name, val, obs_date) ON v.name = s.name
WHERE NOT EXISTS (
    SELECT 1 FROM observations o
    WHERE o.entity_type = 'spot' AND o.entity_id = s.id
      AND o.metric = 'social_mentions' AND o.observed_at = v.obs_date
);
