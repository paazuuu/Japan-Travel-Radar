# 08 — MVP6 AI旅行プランナー仕様

## 目的

ユーザー条件から、DBの実データだけを利用して旅行計画を作る。

## 入力

```text
出発地
日付
日数
予算
人数
旅行タイプ
移動手段
目的
食事条件
宿泊条件
歩行量
```

## 例

```text
出発地: 大阪
日数: 日帰り
予算: 5000円
移動: 電車
目的: 絶景
食事: 魚
人数: 2
```

## Planner Pipeline

```text
User Request
 ↓
Constraint Parser
 ↓
Geospatial Search
 ↓
Candidate Ranking
 ↓
Opening/Date Validation
 ↓
Food Search
 ↓
Route Calculation
 ↓
Budget Calculation
 ↓
LLM Plan Generation
 ↓
Validation
 ↓
Final Plan
```

## AIに渡すデータ

AIには候補スポットの構造化データを渡す。

```text
spot
distance
travel_time
opening_info
estimated_cost
restaurant
restaurant_cost
```

AIがDBに存在しない場所を追加することは禁止。

## 出力

```text
旅行概要

08:00 出発
10:00 観光
12:00 昼食
14:00 観光
16:30 カフェ
18:00 帰宅

予算
交通 ¥xxx
食事 ¥xxx
入場 ¥xxx
合計 ¥xxx

使用した情報源
...
```

## 検証

AI生成後にBackendが:

- 営業時間
- 日付
- 予算
- 移動時間
- 店舗存在
- スポット存在

を再検証する。

## 完了条件

「大阪発・日帰り・5000円・車なし・魚・絶景」のプランを生成でき、各候補に出典がある。
