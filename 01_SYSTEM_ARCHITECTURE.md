# 01 — システム全体構成仕様

## 1. システム概要

```text
                         外部情報源
┌────────────────────────────────────────────────────┐
│ 観光協会 / 自治体 / オープンデータ / Web / YouTube │
│ イベント / 天気 / 飲食店 / 許可されたSNSデータ    │
└──────────────────────┬─────────────────────────────┘
                       ↓
              ┌─────────────────┐
              │ Data Collector   │
              │ 収集・取得       │
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │ Normalizer      │
              │ 正規化・重複排除 │
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │ AI Analyzer     │
              │ 要約・タグ・分類 │
              └────────┬────────┘
                       ↓
              ┌─────────────────┐
              │ PostgreSQL      │
              │ + PostGIS       │
              └────────┬────────┘
                       ↓
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
   Ranking          Map/Search       Planner
       ↓               ↓                ↓
       └───────────────┼────────────────┘
                       ↓
                 FastAPI Backend
                       ↓
                 Next.js Web
                       ↓
             PWA / Native App
```

## 2. コンポーネント

### Frontend
Next.js + TypeScript。ダッシュボード、地図、スポット詳細、ランキング、旅行プランナーを提供。

### Backend
FastAPI。認証、検索、スポット取得、ランキング、AIプラン生成、管理APIを担当。

### Database
PostgreSQL + PostGIS。地理検索、スポット、店舗、イベント、ソース、トレンドスコアを保存。

### Collector
Python。API、RSS、公開ページ、オープンデータ等から情報を取得。

### AI Analyzer
LLMを利用して、要約、分類、タグ付け、食条件判定、季節性評価、コンテンツ生成を行う。

### Scheduler
最初はcronまたはAPScheduler。将来はCelery/Redis等へ拡張可能。

### Object Storage
画像等はDBに直接保存せず、URLまたはオブジェクトストレージを利用。

## 3. ネットワーク

```text
Internet
   ↓
Reverse Proxy
   ↓
Frontend / Backend
   ↓
Private Docker Network
   ├── PostgreSQL
   ├── Collector
   └── AI Worker
```

DBは外部公開しない。

## 4. 設計原則

1. Source of TruthはDB。
2. AI生成文は原情報と区別する。
3. 収集データには出典を付ける。
4. SNS情報は利用規約/API条件を満たす方法だけ使用する。
5. 外部APIキーは環境変数で管理。
6. 全国展開を前提に `prefecture_id`、`region_id` を持つ。
7. 旅行プランは再現可能な入力条件を保存する。
