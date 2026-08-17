# Japan Travel AI Radar — 仕様書セット

## 目的
本プロジェクトは、日本国内の旅行・観光・グルメ・SNSトレンド情報を収集・正規化・AI分析し、「今行く価値のある場所」を発見できる個人向け旅行インテリジェンス基盤を構築する。

最初は自分用のWebシステムとして開始し、データと機能が成熟した段階でPWA、iOS/Android、一般公開サービスへ拡張する。

## 仕様書の読み方

| ID | ファイル | 内容 |
|---|---|---|
| 00 | README | 全体説明・開発順序 |
| 01 | SYSTEM_ARCHITECTURE | 全体構成・責務 |
| 02 | MVP0_INFRASTRUCTURE | Docker・開発環境 |
| 03 | MVP1_DATABASE | PostgreSQL/PostGIS DB |
| 04 | MVP2_COLLECTOR | 情報収集エンジン |
| 05 | MVP3_AI_ANALYSIS | AI分析・タグ・要約 |
| 06 | MVP4_RANKING | トレンド・ランキング |
| 07 | MVP5_MAP_WEB | 地図・Web UI |
| 08 | MVP6_TRAVEL_PLANNER | AI旅行プランナー |
| 09 | MVP7_CHINESE_CONTENT | 中国SNS向けコンテンツ |
| 10 | MVP8_PWA | スマホWebアプリ化 |
| 11 | FUTURE_NATIVE_APP | iOS/Android拡張 |
| 12 | DATA_GOVERNANCE | 情報源・品質・規約 |
| 13 | API_SPEC | Backend API |
| 14 | DEVELOPMENT_PLAN | 実装順序・完了条件 |
| 15 | ENVIRONMENT | 環境変数・秘密情報管理 |

## 推奨開発順

```text
MVP0
 ↓
MVP1 DB
 ↓
MVP2 収集
 ↓
MVP3 AI分析
 ↓
MVP4 Ranking
 ↓
MVP5 Map/Web
 ↓
MVP6 Planner
 ↓
MVP7 中国語コンテンツ
 ↓
MVP8 PWA
 ↓
Native App
```

## MVPの基本方針

- 最初は関西を対象地域とする。
- 最初からSNS全体を直接スクレイピングしない。
- 公式・公開・許可されたデータソースを優先する。
- AIは「事実の保存場所」ではなく、DBに保存された情報を分析・要約・組み合わせる役割とする。
- すべての重要データに `source_url`、`source_type`、`collected_at` を持たせる。
- 将来の全国展開を妨げないスキーマにする。
- Docker Composeでローカル/VPSの両方に再現可能な環境を作る。

## MVP成功条件

「大阪から日帰り、予算5,000円、景色重視、魚料理、車なし」のような条件を入力すると、DBに登録されたスポットと飲食店から、根拠付きの旅行プランを生成できること。
