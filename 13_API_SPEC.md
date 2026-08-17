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
```

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
