# Japan-Travel-Radar

日本国内の旅行・観光・グルメ・SNSトレンド情報を収集・正規化・AI分析し、「今行く価値のある場所」を発見する個人向け旅行インテリジェンス基盤。

仕様書は `00_README.md` を起点に `01`〜`17` を参照してください。

## 開発状況

推奨開発順（`00_README.md`）に沿って一つずつ進めています。

計画は planning-with-files 方式で `task_plan.md` / `progress.md` / `findings.md` に永続化しています。

- [x] **MVP0 — 開発基盤 / Docker環境**
- [x] **MVP1 — DB (PostgreSQL/PostGIS スキーマ・地理検索・関西seed)**
- [x] **MVP2 — 収集エンジン (sources5種 / normalize / dedup / validate / logs)**
- [x] **MVP3 — AI分析 (要約・分類・タグ・季節・食属性・confidence・人間override)**
- [x] **MVP4 — Ranking (Trend Score・急上昇・季節・食・内訳)**
- [x] **MVP5 — Map/Web UI (Dashboard/Map/Ranking/Food/Spot/Admin)**
- [x] **MVP6 — AI旅行プランナー (制約解析→地理検索→ルート→予算→根拠付きプラン)**
- [ ] MVP7 — 中国語コンテンツ / MVP8 — PWA（次のステップ）

> MVP成功条件（`00_README.md`）:「大阪発・日帰り・5,000円・車なし・魚・絶景」の
> 根拠付きプラン生成を実装済み（`./scripts/plan.sh` または `/planner` 画面）。
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

# 4. MVP1: コアスキーマ + 関西seed を投入し、地理検索を確認
./scripts/seed.sh
curl "http://localhost:8000/api/v1/spots/nearby?lat=34.6873&lng=135.5259&radius=3000"
curl "http://localhost:8000/api/v1/restaurants/nearby?lat=34.6687&lng=135.5013&fish=true"
curl "http://localhost:8000/api/v1/search?q=京都"
```

### API (MVP1, base `/api/v1`)

| Method | Path | 説明 |
|---|---|---|
| GET | `/spots` | 一覧（category / prefecture_id / pagination） |
| GET | `/spots/{id}` | 詳細 |
| GET | `/spots/nearby` | 近傍検索（lat/lng/radius[m]、距離順） |
| GET | `/restaurants` | 一覧（category / fish フィルタ） |
| GET | `/restaurants/nearby` | 近傍検索（fish / local_specialty / max_price） |
| GET | `/search?q=` | スポット名・説明の部分一致検索 |

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
