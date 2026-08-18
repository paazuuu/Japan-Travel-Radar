# Task Plan: Japan Travel AI Radar

> planning-with-files 方式で開発全体を管理する。00_README.md の推奨開発順に沿って
> MVP0 → MVP8 を一つずつ実装・コミット・push する。

## Goal
関西を対象に、DB登録済みのスポット/飲食店から根拠付きの旅行プランを生成できる
「最初の実用MVP」（関西100スポット + 50飲食店 + 5情報源 + AIタグ + Trend Score + Dashboard）を完成させる。

## Next Step
MVP6 まで完了・push済み。MVP成功条件（根拠付き旅行プラン生成）を実装で満たした。
次はユーザー指示待ち（候補: MVP7 中国語コンテンツ / MVP8 PWA）。

## Current Phase
Phase 7 (MVP6: Planner) — complete

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
- [x] Collector / Normalizer / Deduplicator / Validator / Runner / Logs
- [x] sources 5種(tourism/government/events opendata + rss + youtube)、fixtures
- [x] raw_items / collector_runs / collection_errors、spots に provenance列
- **Status:** complete

### Phase 4: MVP3 — AI Analysis
- [x] Summary / Category / Tags / Season / Travel type / Food attributes / Confidence
- [x] structured output固定、spot_analyses で原情報と分離、人間override(admin)
- **Status:** complete

### Phase 5: MVP4 — Ranking
- [x] Trend score(重み式) / Growth / Ranking / Category ranking / Daily update
- [x] observations / trend_scores(内訳) / is_reference、admin内訳、rankings API
- **Status:** complete

### Phase 6: MVP5 — Map / Web
- [x] Dashboard / Map(Leaflet+OSM) / Spot detail / Ranking / Food / Admin
- [x] モバイル優先、出典/更新日時表示、AI要約と公式情報の区別、build成功
- **Status:** complete

### Phase 7: MVP6 — Travel Planner
- [x] Constraint parsing(purpose→tags) / Candidate search(地理+タグ+trend)
- [x] Route(nearest-neighbor) / Budget(交通・食事・入場) / 検証 / Saved plan
- [x] travel_plans/items、POST /planner/generate・GET /planner/{id}、/planner UI
- [x] DBの実データのみ・各項目に出典（存在しない場所は追加しない）
- **Status:** complete

### Phase 8: MVP7 — Chinese Content
- [x] Simplified Chinese / Xiaohongshu / WeChat / 60秒Video script / Human review
- [x] content_drafts、fact抽出→翻訳(term map)→整形、下書きのみ・自動公開なし
- [x] API /content/{xiaohongshu,wechat,video-script,chinese}、/content UI
- **Status:** complete

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
