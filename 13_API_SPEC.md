# 13 — Backend API仕様

## Base

```text
/api/v1
```

## Health

```http
GET /health
```

## Spots

```http
GET /spots
GET /spots/{id}
POST /spots
PATCH /spots/{id}
DELETE /spots/{id}
```

## Search

```http
GET /search?q=京都
GET /search?q=紅葉&category=nature&limit=20
```

- `pg_trgm` のトライグラム類似度で検索（誤字・表記ゆれに強い。例: `有馬温線` → 有馬温泉）。
- 対象: `name` / `name_en` / `description` / AIタグ（完全一致）。
- 関連度順に返す（名前の部分一致・AIタグ一致を加点）。結果はAI要約・タグ付き。

## Similar（似たスポット）

```http
GET /spots/{id}/similar?limit=6
```

- コンテンツベース推薦: 共通AIタグ（×3）＋共通旅行タイプ（×1）＋同カテゴリ（+2）＋近さ（〜100km で最大 +1）。
- 自分自身は含まない。存在しない `id` は `404`。

## Nearby

```http
GET /spots/nearby?lat=...&lng=...&radius=...
```

## Ranking

```http
GET /rankings/trending
GET /rankings/popular
GET /rankings/seasonal
GET /rankings/food
```

## Restaurants

```http
GET /restaurants
GET /restaurants/{id}
GET /restaurants/nearby
```

## Planner

```http
POST /planner/generate
GET /planner/{id}
```

## Content

```http
POST /content/chinese
POST /content/xiaohongshu
POST /content/video-script
```

## Admin

```http
GET /admin/sources
GET /admin/collector-runs
GET /admin/ai-jobs
GET /admin/errors
```

## API原則

- JSON
- UUID
- pagination
- filtering
- sorting
- rate limit
- authentication
- audit log
