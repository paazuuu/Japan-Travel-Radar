# Task Plan: Japan Travel AI Radar

> planning-with-files 方式で開発全体を管理する。00_README.md の推奨開発順に沿って
> MVP0 → MVP8 を一つずつ実装・コミット・push する。

## Goal
関西を対象に、DB登録済みのスポット/飲食店から根拠付きの旅行プランを生成できる
「最初の実用MVP」（関西100スポット + 50飲食店 + 5情報源 + AIタグ + Trend Score + Dashboard）を完成させる。

## Next Step
MVP2（Phase 3）: 情報収集エンジン（Collector/Scheduler/Normalizer/Deduplicator/
Validator/Logs）を実装し、seed を実データ収集へ拡張する（スポット100件+へ）。

## Current Phase
Phase 3 (MVP2: Collector) — 次に着手

## Phases

### Phase 1: MVP0 — 開発基盤 / Docker
- [x] docker-compose (postgres/PostGIS, backend, frontend, collector, worker)
- [x] FastAPI backend + /health (DB + PostGIS 確認)
- [x] Next.js frontend (health 表示)
- [x] PostGIS 初期化マイグレーション, .env.example, tests
- [x] コミット & push (branch: claude/readme-plan-execution-ia7sea)
- **Status:** complete

### Phase 2: MVP1 — Database
- [x] スキーマ設計 (Region, Prefecture, City, Source, Spot, Restaurant, Event, tags)
- [x] PostGIS geography(Point,4326) と GiST index
- [x] マイグレーション SQL (database/migrations/0002_core_schema.sql)
- [x] SQLAlchemy モデル (backend/app/models.py)
- [x] 近傍検索 API (/api/v1/spots/nearby, /restaurants/nearby, /search)
- [x] 関西 seed data（代表24スポット + 12飲食店 + provenance）
- [ ] スポット100件+ へ拡張（→ MVP2 collector / 追加投入で対応）
- **Status:** complete（100件到達は MVP2 へ委譲）

### Phase 3: MVP2 — Collector
- [ ] Collector / Scheduler / Normalizer / Deduplicator / Validator / Logs
- **Status:** in_progress（次に着手）

### Phase 4: MVP3 — AI Analysis
- [ ] Summary / Category / Tags / Season / Food attributes / Confidence / Human override
- **Status:** pending

### Phase 5: MVP4 — Ranking
- [ ] Trend score / Growth / Ranking / Category ranking / Daily update
- **Status:** pending

### Phase 6: MVP5 — Map / Web
- [ ] Dashboard / Map / Spot detail / Ranking / Search / Filters
- **Status:** pending

### Phase 7: MVP6 — Travel Planner
- [ ] Constraint parsing / Candidate search / Route / Budget / Validation / Saved plan
- **Status:** pending

### Phase 8: MVP7 — Chinese Content
- [ ] Simplified Chinese / Xiaohongshu / WeChat / Video script / Human review
- **Status:** pending

### Phase 9: MVP8 — PWA
- [ ] Mobile UI / Installable / Favorites / Saved plans / Share
- **Status:** pending

## Key Questions
1. seed データはどこまで実データを入れるか？（MVP1では代表的な少数の実在スポットで十分）
2. スキーマは全国展開を妨げないか？（prefecture_id / region_id を保持すること）

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| GitHub への反映は MCP ではなく git push | App 権限付与後は直接 push が通る（MVP0で確認） |
| planning-with-files をリポジトリにコミット | 長期プロジェクトのロードマップとして永続化したい |
| PostGIS geography(Point,4326) を採用 | 仕様準拠。距離をメートルで扱え近傍検索(ST_DWithin)が簡潔 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| git push / GitHub API が 403 | 1 | Claude GitHub App が未インストールだった。App をリポジトリにインストールし解決 |

## Notes
- 各 MVP 完了ごとにコミット & push する（branch: claude/readme-plan-execution-ia7sea）
- すべての重要データに source_url, source_type, collected_at を持たせる
- DB はインターネット非公開（private network のみ）
