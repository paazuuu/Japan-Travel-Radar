-- Feature A: seed the events table with representative Kansai festivals.
-- (The collector also populates events from the events source; this makes the
--  events UI usable without a collector run.) Re-run safe via NOT EXISTS.

INSERT INTO events (name, description, prefecture_id, location, category, subcategory,
                    start_at, end_at, official_url, source_id, source_url, source_key, external_id)
SELECT
    v.name, v.description,
    (SELECT id FROM prefectures WHERE code = v.pref_code),
    ST_SetSRID(ST_MakePoint(v.lng, v.lat), 4326)::geography,
    'event', v.subcategory, v.start_at::timestamptz, v.end_at::timestamptz, v.url,
    (SELECT id FROM sources WHERE source_name = 'Manual seed (MVP1 curated Kansai set)' LIMIT 1),
    v.url, 'events_seed', v.external_id
FROM (VALUES
    ('e-gion', '祇園祭', '京都・八坂神社の夏祭り。', '26', 135.7681, 35.0037, 'festival', '2026-07-01', '2026-07-31', 'https://www.gionmatsuri.or.jp/'),
    ('e-tenjin', '天神祭', '大阪天満宮の夏祭り・船渡御。', '27', 135.5122, 34.6949, 'festival', '2026-07-24', '2026-07-25', NULL),
    ('e-kishiwada', '岸和田だんじり祭', '勇壮なだんじりの祭り。', '27', 135.3710, 34.4600, 'festival', '2026-09-12', '2026-09-13', NULL),
    ('e-nara-omizutori', '東大寺 お水取り', '二月堂の修二会。', '29', 135.8430, 34.6890, 'festival', '2026-03-01', '2026-03-14', NULL),
    ('e-kobe-luminarie', '神戸ルミナリエ', '冬の光の祭典。', '28', 135.1930, 34.6900, 'illumination', '2026-01-30', '2026-02-08', NULL),
    ('e-arashiyama-hanatouro', '嵐山花灯路', '嵐山一帯の灯りイベント。', '26', 135.6770, 35.0094, 'illumination', '2026-12-11', '2026-12-20', NULL),
    ('e-nachi-fire', '那智の扇祭り', '熊野那智大社の火祭り。', '30', 135.8900, 33.6680, 'festival', '2026-07-14', '2026-07-14', NULL),
    ('e-otsu', '大津祭', 'からくり山車の祭り。', '25', 135.8650, 35.0040, 'festival', '2026-10-10', '2026-10-11', NULL)
) AS v(external_id, name, description, pref_code, lng, lat, subcategory, start_at, end_at, url)
WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.source_key = 'events_seed' AND e.external_id = v.external_id);
