# 14 — 開発ロードマップ・MVP完了条件

## Stage 0

### ゴール
Docker環境が完成。

### Done
- [ ] Git repository
- [ ] Docker Compose
- [ ] PostgreSQL/PostGIS
- [ ] FastAPI
- [ ] Next.js
- [ ] Health check
- [ ] .env管理

## Stage 1

### ゴール
旅行DB完成。

### Done
- [ ] Spot
- [ ] Restaurant
- [ ] Event
- [ ] Source
- [ ] Region
- [ ] PostGIS検索
- [ ] Seed data

## Stage 2

### ゴール
自動収集。

### Done
- [ ] Collector
- [ ] Scheduler
- [ ] Normalizer
- [ ] Deduplicator
- [ ] Validator
- [ ] Logs

## Stage 3

### ゴール
AI分析。

### Done
- [ ] Summary
- [ ] Category
- [ ] Tags
- [ ] Season
- [ ] Food attributes
- [ ] Confidence
- [ ] Human override

## Stage 4

### ゴール
Trend Radar。

### Done
- [ ] Trend score
- [ ] Growth
- [ ] Ranking
- [ ] Category ranking
- [ ] Daily update

## Stage 5

### ゴール
Web旅行探索。

### Done
- [ ] Dashboard
- [ ] Map
- [ ] Spot detail
- [ ] Ranking
- [ ] Search
- [ ] Filters

## Stage 6

### ゴール
AI旅行プランナー。

### Done
- [ ] Constraint parsing
- [ ] Candidate search
- [ ] Route
- [ ] Budget
- [ ] Validation
- [ ] Saved plan

## Stage 7

### ゴール
中国語コンテンツ。

### Done
- [ ] Simplified Chinese
- [ ] Xiaohongshu draft
- [ ] WeChat article
- [ ] Video script
- [ ] Human review

## Stage 8

### ゴール
PWA。

### Done
- [ ] Mobile UI
- [ ] Installable
- [ ] Favorites
- [ ] Saved plans
- [ ] Share

## Stage 9

### ゴール
一般公開。

追加:

- Authentication
- User accounts
- Multi-region
- Recommendation learning
- Analytics
- Billing if needed

## Stage 10

### ゴール
Native App。

React Native/Expo等を検討。

## 最初の実装対象

最初は以下だけを完成させる。

```text
関西100スポット
+
50飲食店
+
5情報源
+
AIタグ
+
Trend Score
+
Dashboard
```

これを「最初の実用MVP」とする。
