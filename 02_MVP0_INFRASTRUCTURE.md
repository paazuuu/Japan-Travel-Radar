# 02 — MVP0 開発基盤仕様

## 目的

ローカルPCとVPSの双方で同じ構成を再現できる開発基盤を作る。

## 技術

- Docker
- Docker Compose
- Python 3.12+
- FastAPI
- PostgreSQL 16+
- PostGIS
- Next.js
- TypeScript
- Git
- Nginx/Caddy等のReverse Proxy

## コンテナ

```text
traefik/nginx
frontend
backend
collector
worker
postgres
```

RedisはMVP0では必須ではない。ジョブ量が増えた時点で追加する。

## 推奨ディレクトリ

```text
japan-travel-radar/
├── docker-compose.yml
├── .env.example
├── backend/
├── frontend/
├── collector/
├── worker/
├── database/
│   └── migrations/
├── scripts/
├── docs/
└── tests/
```

## 必須環境変数

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DATABASE_URL
AI_API_KEY
MAPS_API_KEY
APP_ENV
SECRET_KEY
```

`.env` はGitへコミットしない。

## 完了条件

- `docker compose up -d` で起動する
- Backendのhealth endpointが200
- PostgreSQLへ接続できる
- PostGIS extensionが有効
- FrontendからBackend APIへ接続できる
- DBポートをインターネットへ公開しない
