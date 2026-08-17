# 03 — MVP1 旅行データベース仕様

## 対象

最初は関西圏を対象とする。

- 大阪
- 京都
- 兵庫
- 奈良
- 滋賀
- 和歌山
- 必要に応じて三重

## ER概念図

```text
regions
   │
   ├── prefectures
   │       │
   │       └── cities
   │               │
   │               ├── spots
   │               ├── restaurants
   │               └── events
   │
sources ──< source_items >── spots
spots ──< spot_tags
spots ──< spot_scores
restaurants ──< food_tags
```

## spots

```text
id UUID PK
name TEXT
name_en TEXT NULL
name_zh TEXT NULL
description TEXT
prefecture_id
city_id
location GEOGRAPHY(POINT, 4326)
category
subcategory
best_season
recommended_stay_minutes
estimated_budget_min
estimated_budget_max
access_text
official_url
source_id
source_url
status
created_at
updated_at
```

## restaurants

```text
id UUID PK
name
location GEOGRAPHY(POINT,4326)
category
price_min
price_max
fish BOOLEAN
meat BOOLEAN
vegetarian BOOLEAN
vegan BOOLEAN
local_specialty BOOLEAN
reservation_url
official_url
source_url
updated_at
```

## sources

```text
id UUID PK
source_type
source_name
source_url
license_note
collection_method
last_collected_at
```

## trend_scores

```text
id
spot_id
score_date
trend_score
growth_score
social_score
seasonal_score
novelty_score
confidence
```

## events

```text
id
name
location
start_at
end_at
category
official_url
source_url
```

## food_tags

```text
restaurant_id
tag
confidence
source_url
```

## 必須インデックス

- location GIST
- prefecture_id
- city_id
- category
- updated_at
- trend_score + score_date

## データ品質

必須項目が欠けたレコードは公開ランキング対象から除外可能にする。

## 完了条件

- 関西のテストスポット100件以上を登録
- 地理検索が動作
- 近隣店舗検索が動作
- 出典URLを確認可能
