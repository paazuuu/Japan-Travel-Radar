# 04 — MVP2 情報収集エンジン仕様

## 目的

外部の旅行情報を定期的に取得し、DBへ安全に取り込む。

## 収集対象の優先順位

### Tier 1
- 自治体
- 観光協会
- 公的オープンデータ
- 公式イベントページ

### Tier 2
- 旅行関連Web
- ニュース
- RSS
- YouTube等の公開情報

### Tier 3
- SNSの公式API・許可されたデータ提供手段

直接スクレイピングは、利用規約・robots.txt・アクセス制限・著作権等を確認し、許可された範囲だけで行う。

## Collector構成

```text
collector/
├── sources/
│   ├── tourism/
│   ├── government/
│   ├── events/
│   ├── youtube/
│   └── rss/
├── normalizer.py
├── deduplicator.py
├── validator.py
└── runner.py
```

## Pipeline

```text
Fetch
 ↓
Raw保存
 ↓
Parse
 ↓
Normalize
 ↓
Deduplicate
 ↓
Validate
 ↓
DB登録
 ↓
AI分析待ち
```

## Raw Data

取得した元情報は、可能なら原文全体を長期保存するのではなく、必要なメタデータ・URL・取得日時・ハッシュ等を保存する。

## 重複判定

候補キー:

- 公式URL
- 正規化名称
- 座標距離
- 電話番号等の公開識別情報
- 外部ID

## 更新頻度

- イベント: 1日数回
- 観光スポット: 1日1回〜数日に1回
- 店舗: 1日〜数日
- トレンド: 日次
- 静的地域情報: 週次

## エラー処理

- HTTPエラー
- タイムアウト
- レート制限
- Parserエラー
- AIエラー

を個別に記録。

## 完了条件

- 5種類以上の合法的な情報源から取得
- 日次ジョブが成功
- 重複登録が抑制される
- 失敗ログが確認できる
- 収集元URLを追跡できる
