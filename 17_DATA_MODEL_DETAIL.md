# 17 — データモデル詳細

## Spot

スポットは「旅行先として訪問可能な地点」を表す。

## Restaurant

飲食店はSpotと独立して管理する。理由は店舗の営業時間・価格・食属性が変化するため。

## Source

外部情報の出典を表す。

## Observation

トレンドは現在値だけでなく時系列で保存する。

```text
observations
id
entity_type
entity_id
metric
value
observed_at
source_id
```

例:

```text
spot123
social_mentions
125
2026-08-17
source456
```

これにより「昨日100→今日125」のような変化を計算できる。

## Recommendation

AIが生成した推薦理由を保存する。

```text
recommendations
id
spot_id
reason
score
model
generated_at
```

## Travel Plan

```text
travel_plans
id
origin
start_date
days
budget
party_size
transport
preferences
generated_at
```

## Travel Plan Item

```text
travel_plan_items
id
plan_id
sequence
spot_id
restaurant_id
start_time
end_time
estimated_cost
travel_time
```

この構造により、後からプランを編集できる。
