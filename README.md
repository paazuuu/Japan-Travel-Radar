# Japan-Travel-Radar

日本国内の旅行・観光・グルメ・SNSトレンド情報を収集・正規化・AI分析し、「今行く価値のある場所」を発見する個人向け旅行インテリジェンス基盤。

仕様書は `00_README.md` を起点に `01`〜`17` を参照してください。

## 開発状況

推奨開発順（`00_README.md`）に沿って一つずつ進めています。

- [x] **MVP0 — 開発基盤 / Docker環境**（本ドキュメントのセットアップ対象）
- [ ] MVP1 — DB (PostgreSQL/PostGIS スキーマ)
- [ ] MVP2 — 収集エンジン
- [ ] MVP3 — AI分析
- [ ] MVP4 — Ranking
- [ ] MVP5 — Map/Web
- [ ] MVP6 — Planner
- [ ] MVP7 — 中国語コンテンツ
- [ ] MVP8 — PWA

## 構成 (MVP0)

```text
japan-travel-radar/
├── docker-compose.yml     # postgres / backend / frontend / collector / worker
├── .env.example           # 環境変数テンプレート（.env はコミットしない）
├── backend/               # FastAPI (/health で DB+PostGIS を確認)
├── frontend/              # Next.js + TypeScript (backend health を表示)
├── collector/             # 収集サービス雛形 (MVP2 で実装)
├── worker/                # バックグラウンドジョブ雛形
├── database/migrations/   # DB 初期化 SQL (PostGIS 有効化)
├── scripts/               # 補助スクリプト
├── docs/
└── tests/
```

## セットアップ

```bash
# 1. 環境変数を用意（パスワード等を実値に）
cp .env.example .env

# 2. 起動
docker compose up -d --build

# 3. 動作確認
curl http://localhost:8000/health      # backend + DB + PostGIS
open  http://localhost:3000            # frontend が health を表示
```

### 完了条件 (02_MVP0_INFRASTRUCTURE.md)

- `docker compose up -d` で起動する
- Backend の `/health` が 200
- PostgreSQL へ接続でき、PostGIS extension が有効
- Frontend から Backend API へ接続できる
- DB ポートはインターネットへ公開しない（`postgres` は internal な private network のみ）

## テスト

```bash
pip install -r backend/requirements.txt httpx pytest
pytest tests/
```
