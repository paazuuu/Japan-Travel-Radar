-- MVP1 seed: Kansai region reference data + representative real spots/restaurants.
-- Idempotent-ish: safe to re-run (ON CONFLICT on natural keys / name+prefecture).
-- Coordinates are WGS84 (lng, lat). Provenance recorded via sources + source_url.

-- ---------------------------------------------------------------------------
-- Region + prefectures
-- ---------------------------------------------------------------------------
INSERT INTO regions (code, name, name_en) VALUES
    ('kansai', '関西', 'Kansai')
ON CONFLICT (code) DO NOTHING;

INSERT INTO prefectures (region_id, code, name, name_en)
SELECT r.id, v.code, v.name, v.name_en
FROM regions r
CROSS JOIN (VALUES
    ('27', '大阪府', 'Osaka'),
    ('26', '京都府', 'Kyoto'),
    ('28', '兵庫県', 'Hyogo'),
    ('29', '奈良県', 'Nara'),
    ('25', '滋賀県', 'Shiga'),
    ('30', '和歌山県', 'Wakayama')
) AS v(code, name, name_en)
WHERE r.code = 'kansai'
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Seed source (provenance for these curated records)
-- ---------------------------------------------------------------------------
INSERT INTO sources (source_type, source_name, source_url, license_note, collection_method)
SELECT
    'manual',
    'Manual seed (MVP1 curated Kansai set)',
    'https://github.com/paazuuu/japan-travel-radar',
    'Representative sample data for development; verify before public use.',
    'manual'
WHERE NOT EXISTS (
    SELECT 1 FROM sources WHERE source_name = 'Manual seed (MVP1 curated Kansai set)'
);

-- ---------------------------------------------------------------------------
-- Spots
-- ---------------------------------------------------------------------------
INSERT INTO spots
    (name, name_en, description, prefecture_id, location, category, subcategory,
     best_season, recommended_stay_minutes, estimated_budget_min, estimated_budget_max,
     access_text, source_id, source_url, status)
SELECT
    v.name, v.name_en, v.description,
    (SELECT id FROM prefectures WHERE code = v.pref_code),
    ST_SetSRID(ST_MakePoint(v.lng, v.lat), 4326)::geography,
    v.category, v.subcategory, v.best_season, v.stay, v.bmin, v.bmax, v.access,
    (SELECT id FROM sources WHERE source_name = 'Manual seed (MVP1 curated Kansai set)' LIMIT 1),
    'https://github.com/paazuuu/japan-travel-radar',
    'published'
FROM (VALUES
    -- Osaka (27)
    ('大阪城', 'Osaka Castle', '大阪のシンボル。天守閣と公園。', '27', 135.5259, 34.6873, 'sightseeing', 'castle', 'spring', 120, 600, 1500, 'JR大阪城公園駅 徒歩'),
    ('通天閣', 'Tsutenkaku', '新世界のランドマークタワー。', '27', 135.5063, 34.6525, 'sightseeing', 'tower', 'all', 60, 900, 1500, '地下鉄 動物園前/恵美須町'),
    ('海遊館', 'Osaka Aquarium Kaiyukan', '世界最大級の水族館。', '27', 135.4289, 34.6545, 'sightseeing', 'aquarium', 'all', 150, 2700, 2700, '地下鉄 大阪港駅 徒歩'),
    ('道頓堀', 'Dotonbori', 'グルメと看板の繁華街。', '27', 135.5013, 34.6687, 'gourmet', 'street', 'all', 90, 1000, 5000, '地下鉄 なんば駅'),
    ('万博記念公園', 'Expo 70 Commemorative Park', '太陽の塔と広大な公園。', '27', 135.5300, 34.8073, 'nature', 'park', 'spring', 120, 260, 260, '大阪モノレール 万博記念公園駅'),
    -- Kyoto (26)
    ('清水寺', 'Kiyomizu-dera', '世界遺産の名刹。清水の舞台。', '26', 135.7850, 34.9949, 'sightseeing', 'temple', 'autumn', 90, 400, 400, '市バス 清水道 徒歩'),
    ('伏見稲荷大社', 'Fushimi Inari Taisha', '千本鳥居で有名。', '26', 135.7727, 34.9671, 'sightseeing', 'shrine', 'all', 120, 0, 0, 'JR稲荷駅 すぐ'),
    ('金閣寺', 'Kinkaku-ji', '金色の舎利殿。世界遺産。', '26', 135.7292, 35.0394, 'sightseeing', 'temple', 'winter', 60, 500, 500, '市バス 金閣寺道'),
    ('嵐山 竹林の小径', 'Arashiyama Bamboo Grove', '幻想的な竹林。', '26', 135.6710, 35.0170, 'nature', 'scenery', 'autumn', 60, 0, 0, 'JR嵯峨嵐山駅 徒歩'),
    ('二条城', 'Nijo Castle', '徳川の城。世界遺産。', '26', 135.7481, 35.0142, 'sightseeing', 'castle', 'spring', 90, 1300, 1300, '地下鉄 二条城前駅'),
    -- Hyogo (28)
    ('姫路城', 'Himeji Castle', '白鷺城。国宝・世界遺産。', '28', 134.6939, 34.8394, 'sightseeing', 'castle', 'spring', 120, 1000, 1000, 'JR姫路駅 徒歩'),
    ('有馬温泉', 'Arima Onsen', '日本三古湯のひとつ。', '28', 135.2470, 34.7975, 'onsen', 'hotspring', 'winter', 240, 800, 20000, '神戸電鉄 有馬温泉駅'),
    ('神戸ハーバーランド', 'Kobe Harborland', '港のショッピング・夜景。', '28', 135.1810, 34.6790, 'sightseeing', 'waterfront', 'all', 120, 0, 5000, 'JR神戸駅 徒歩'),
    ('六甲山', 'Mount Rokko', '神戸の夜景と自然。', '28', 135.2617, 34.7783, 'nature', 'mountain', 'summer', 180, 0, 3000, '六甲ケーブル'),
    -- Nara (29)
    ('東大寺', 'Todai-ji', '奈良の大仏。世界遺産。', '29', 135.8398, 34.6890, 'sightseeing', 'temple', 'autumn', 90, 800, 800, '奈良駅よりバス'),
    ('奈良公園', 'Nara Park', '鹿と自然の公園。', '29', 135.8430, 34.6851, 'nature', 'park', 'autumn', 90, 0, 0, '近鉄奈良駅 徒歩'),
    ('春日大社', 'Kasuga Taisha', '朱塗りと燈籠の古社。世界遺産。', '29', 135.8483, 34.6819, 'sightseeing', 'shrine', 'all', 60, 500, 500, '奈良公園内'),
    -- Shiga (25)
    ('琵琶湖（大津）', 'Lake Biwa (Otsu)', '日本最大の湖。', '25', 135.8686, 35.0036, 'nature', 'lake', 'summer', 120, 0, 3000, 'JR大津駅 徒歩'),
    ('彦根城', 'Hikone Castle', '現存天守の国宝。', '25', 136.2517, 35.2764, 'sightseeing', 'castle', 'spring', 90, 800, 800, 'JR彦根駅 徒歩'),
    ('比叡山延暦寺', 'Enryaku-ji', '天台宗総本山。世界遺産。', '25', 135.8407, 35.0703, 'sightseeing', 'temple', 'autumn', 150, 1000, 1000, '坂本ケーブル'),
    -- Wakayama (30)
    ('高野山 金剛峯寺', 'Koyasan Kongobu-ji', '真言宗の聖地。世界遺産。', '30', 135.5850, 34.2130, 'sightseeing', 'temple', 'autumn', 180, 1000, 5000, '南海高野線 極楽橋よりケーブル'),
    ('那智の滝', 'Nachi Falls', '日本一の落差の滝。世界遺産。', '30', 135.8903, 33.6725, 'nature', 'waterfall', 'summer', 60, 0, 500, 'JR紀伊勝浦駅よりバス'),
    ('白浜', 'Shirahama Beach', '白い砂浜と温泉。', '30', 135.3389, 33.6853, 'nature', 'beach', 'summer', 180, 0, 3000, 'JR白浜駅よりバス'),
    ('アドベンチャーワールド', 'Adventure World', 'パンダで有名なテーマパーク。', '30', 135.3856, 33.6647, 'sightseeing', 'themepark', 'all', 300, 5300, 5300, 'JR白浜駅よりバス')
) AS v(name, name_en, description, pref_code, lng, lat, category, subcategory, best_season, stay, bmin, bmax, access)
WHERE NOT EXISTS (SELECT 1 FROM spots s WHERE s.name = v.name);

-- ---------------------------------------------------------------------------
-- Restaurants
-- ---------------------------------------------------------------------------
INSERT INTO restaurants
    (name, prefecture_id, location, category, price_min, price_max,
     fish, meat, vegetarian, vegan, local_specialty, source_id, source_url)
SELECT
    v.name,
    (SELECT id FROM prefectures WHERE code = v.pref_code),
    ST_SetSRID(ST_MakePoint(v.lng, v.lat), 4326)::geography,
    v.category, v.pmin, v.pmax, v.fish, v.meat, v.veg, v.vegan, v.local,
    (SELECT id FROM sources WHERE source_name = 'Manual seed (MVP1 curated Kansai set)' LIMIT 1),
    'https://github.com/paazuuu/japan-travel-radar'
FROM (VALUES
    ('かに道楽 道頓堀本店', '27', 135.5010, 34.6686, 'seafood', 3000, 10000, true, false, false, false, true),
    ('串カツだるま 新世界総本店', '27', 135.5061, 34.6522, 'kushikatsu', 1500, 3500, false, true, false, false, true),
    ('錦市場の海鮮丼（サンプル）', '26', 135.7649, 35.0050, 'seafood', 1800, 4000, true, false, false, false, true),
    ('京都 湯葉・おばんざい（サンプル）', '26', 135.7681, 35.0116, 'kyoto-cuisine', 2500, 6000, false, false, true, false, true),
    ('神戸牛ステーキ（サンプル）', '28', 135.1949, 34.6913, 'steak', 6000, 18000, false, true, false, false, true),
    ('明石焼き（サンプル）', '28', 134.9937, 34.6494, 'akashiyaki', 800, 2000, true, false, false, false, true),
    ('柿の葉寿司（サンプル）', '29', 135.8300, 34.6800, 'sushi', 1200, 3000, true, false, false, false, true),
    ('三輪そうめん（サンプル）', '29', 135.8530, 34.5290, 'noodles', 900, 2000, false, false, true, false, true),
    ('近江牛レストラン（サンプル）', '25', 136.2500, 35.2800, 'steak', 5000, 15000, false, true, false, false, true),
    ('近江ちゃんぽん（サンプル）', '25', 136.1100, 35.1300, 'noodles', 800, 1800, false, true, false, false, true),
    ('勝浦まぐろ料理（サンプル）', '30', 135.9400, 33.6300, 'seafood', 2000, 6000, true, false, false, false, true),
    ('和歌山ラーメン（サンプル）', '30', 135.1675, 34.2260, 'ramen', 700, 1500, false, true, false, false, true)
) AS v(name, pref_code, lng, lat, category, pmin, pmax, fish, meat, veg, vegan, local)
WHERE NOT EXISTS (SELECT 1 FROM restaurants r WHERE r.name = v.name);
