# Findings & Decisions

## Requirements (00/03/13/17 由来)
- 対象は関西（大阪/京都/兵庫/奈良/滋賀/和歌山、必要に応じ三重）
- 全国展開を妨げないスキーマ（region_id / prefecture_id / city_id を保持）
- すべての重要データに source_url / source_type / collected_at 相当を持たせる
- MVP1 完了条件: 関西スポット登録 / 地理検索 / 近隣店舗検索 / 出典URL確認

## データモデル要点（03 / 17）
- 階層: regions → prefectures → cities →（spots / restaurants / events）
- spots.location / restaurants.location / events.location は **GEOGRAPHY(POINT, 4326)**
  （距離をメートルで扱えるため geometry ではなく geography を採用）
- spots: name(_en/_zh), description, category, subcategory, best_season,
  recommended_stay_minutes, estimated_budget_min/max, access_text, official_url,
  source_id, source_url, status, timestamps
- restaurants: category, price_min/max, fish/meat/vegetarian/vegan/local_specialty(bool),
  reservation_url, official_url, source_url
- sources: source_type, source_name, source_url, license_note, collection_method, last_collected_at
- events: name, location, start_at, end_at, category, official_url, source_url
- spot_tags(spot_id, tag), food_tags(restaurant_id, tag, confidence, source_url)
- 後続: trend_scores(MVP4), observations/recommendations(MVP3-4), travel_plans(MVP6)

## 必須インデックス（03）
- location GIST / prefecture_id / city_id / category / updated_at /（trend_score+score_date は MVP4）

## API（13）
- Base `/api/v1`。MVP1 対象: GET /spots, GET /spots/{id}, GET /spots/nearby,
  GET /restaurants, GET /restaurants/nearby, GET /search?q=

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| location は GEOGRAPHY(POINT,4326) | 仕様準拠。ST_DWithin/ST_Distance がメートルで扱え近傍検索が簡潔 |
| UUID 主キー (gen_random_uuid) | 仕様準拠。pgcrypto は PostGIS イメージに同梱 |
| city は当面 NULL 許容 | MVP1 は prefecture 単位で十分、city マスタは段階導入 |
| seed は実在の代表スポットを中心に投入 | 地理検索の動作実証を優先。100件到達は MVP2 collector / 追加投入で拡張 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| 100件+ の実データ手入力は誤りが入りやすい | MVP1 は代表データで検索を実証、件数拡張は collector 側へ委譲 |

## Resources
- 仕様: 03_MVP1_DATABASE.md, 17_DATA_MODEL_DETAIL.md, 13_API_SPEC.md
- 既存: database/migrations/0001_init_postgis.sql（postgis, pg_trgm 有効化）
