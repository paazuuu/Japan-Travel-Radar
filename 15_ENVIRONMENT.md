# 15 — 環境変数・秘密情報管理

## .env.example

```env
APP_ENV=development

POSTGRES_DB=japan_travel
POSTGRES_USER=travel
POSTGRES_PASSWORD=CHANGE_ME
DATABASE_URL=postgresql://travel:CHANGE_ME@postgres:5432/japan_travel

AI_API_KEY=
MAPS_API_KEY=

SECRET_KEY=CHANGE_ME

FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

## 本番環境

- `.env`をGit管理しない
- 強いランダムパスワード
- DB外部公開禁止
- HTTPS
- Reverse Proxy
- ログ監視
- DBバックアップ
- APIキーのローテーション

## Docker Network

```text
public
  frontend
  backend

private
  postgres
  worker
  collector
```

PostgreSQLはprivate networkのみ。

## Backup

最低限:

```text
daily PostgreSQL dump
weekly full backup
```

バックアップから復元できることを定期的にテストする。
