# Progress Log

## Session: 追加整備（CI / Admin認証 / 実LLM連携）
- **CI**: .github/workflows/ci.yml — PR/push で pytest(backend/collector/worker) +
  frontend build + docker compose config を実行（GitHub上で回る＝実質の動作確認）
- **Admin認証**: app/auth.py の require_admin を /admin ルータ全体に適用。X-Admin-Key
  (ADMIN_API_KEY) 必須、未設定は fail-closed(503)。override は locked に加えキー必須。
  frontend は SSR で ADMIN_API_KEY をヘッダ送信（ブラウザ非公開）
- **実LLM連携**: worker/llm.py・backend/app/llm.py。AI_API_KEY 設定時のみ Anthropic
  (既定 claude-opus-5, AI_MODEL で変更可)。分析(tags/summary)・中国語翻訳・プラン要約を強化。
  未設定/SDK無し/APIエラー時はルールベース/テンプレへ自動フォールバック（創作禁止の制約付き）
- テスト +7（admin auth 4 / llm fallback 4 のうち…計46 passed）。anthropic 未インストールでも
  import・フォールバック動作を確認


## Session: 2026-08-17

### Phase 1: MVP0 — 開発基盤 / Docker
- **Status:** complete
- Actions taken:
  - docker-compose.yml 作成（postgres/PostGIS 16-3.4, backend, frontend, collector, worker）
  - public / private(internal) ネットワーク分離。postgres は private のみ、ポート非公開
  - FastAPI backend と /health（DB接続 + PostGIS_Version 確認、DB無しでも200 degraded）
  - Next.js 15 + TypeScript frontend（backend health を表示、standalone Dockerfile）
  - database/migrations/0001_init_postgis.sql（postgis, pg_trgm）
  - .env.example / .gitignore / scripts/healthcheck.sh / tests / README 更新
  - planning-with-files 方式を導入（task_plan.md / progress.md / findings.md）
- Files created/modified:
  - docker-compose.yml, backend/*, frontend/*, collector/*, worker/*
  - database/migrations/0001_init_postgis.sql, tests/test_backend_health.py
  - .env.example, .gitignore, README.md, scripts/healthcheck.sh
- 結果: commit 067f931 を push 済み

### Phase 2: MVP1 — Database
- **Status:** complete（スポット100件到達は MVP2 collector へ委譲）
- Started/Finished: 2026-08-17
- Actions taken:
  - planning-with-files 方式を導入（task_plan/progress/findings を追加、別リポジトリ paazuuu/planning-with-files を参照）
  - コアスキーマ 0002_core_schema.sql（regions/prefectures/cities/sources/spots/restaurants/events/spot_tags/food_tags）
  - geography(POINT,4326) + GiST/GIN(trgm) インデックス
  - SQLAlchemy モデル（GeoAlchemy2）と DB セッション/Depends(get_db)
  - API /api/v1: spots(list/detail/nearby), restaurants(list/detail/nearby+食属性フィルタ), search
  - 関西 seed（regions/6府県 + 代表24スポット + 12飲食店、source と source_url で出典明示）
  - scripts/seed.sh（コンテナへ schema+seed 投入、件数確認）
- Files created/modified:
  - database/migrations/0002_core_schema.sql, database/seeds/seed_kansai.sql
  - backend/app/{models,schemas,db}.py, backend/app/routers/{spots,restaurants,search}.py
  - backend/app/main.py（ルーター登録）, backend/requirements.txt（geoalchemy2）
  - tests/test_api_routes.py, scripts/seed.sh
  - task_plan.md / progress.md / findings.md（planning-with-files）

### Phase 3-6: MVP2–MVP5（2026-08-17 一括実装）
- **MVP2 収集エンジン:** collector(sources5種/normalizer/dedup/validator/runner)、
  raw_items/collector_runs/collection_errors、fixturesで日次ジョブ成功、provenance列
- **MVP3 AI分析:** worker/analyzer(ルールベース, structured output固定, confidence)、
  spot_analyses(原情報と分離)、spot_tags origin(manual/ai)、admin override/review
- **MVP4 Ranking:** worker/scorer(重み式 Trend Score, 各成分0-100, is_reference)、
  observations/trend_scores、rankings API(trending/rising/new/seasonal/popular/food)、admin内訳
- **MVP5 Web UI:** Next.js App Router — Home/Ranking/Map(Leaflet+OSM)/Food/Spot詳細/Admin、
  モバイル優先、出典・更新日時表示、AI要約と公式情報の区別。`npm run build` 成功(6 routes)
- **テスト:** pytest 19 passed（collector 5 / analyzer 5 / scorer 5 / routes 2 / health 2）
- **検証保留:** docker daemon 不在のため DB実クエリ/collector・worker実行/フロント実起動は未実施。
  ローカルで scripts/{seed,collect,analyze,rank}.sh + docker compose で確認可能。

### 追加: 実データソース（MVP2拡張, 2026-08-17）
- collector に実ソース3種を追加: **OpenStreetMap Overpass(ODbL)**（関西6府県を area 指定・
  座標付きPOI）、**Wikidata SPARQL(CC0)**（観光地×府県×座標）、**設定可能 open-data JSON URL**
  （`OPENDATA_JSON_URLS` で自治体データを差し込み）
- パーサ(parse_elements / parse_bindings)は実API同形サンプルで単体テスト（+3, 計32 passed）
- ネットワーク失敗は collection_errors に記録し degrade、fixture で日次ジョブは成功維持
- COLLECTOR_DISABLE_NETWORK / OVERPASS_URL / WIKIDATA_URL 等を .env.example に追加、
  docs/DATA_SOURCES.md にライセンス・帰属・設定を記載
- 注意: このサンドボックスは egress で overpass/wikidata が 403（実フェッチ不可）。
  実データ投入は通常の docker 実行環境で `./scripts/collect.sh`
- 追加: 自治体オープンデータの列名マッピング（`opendata_datasets` ソース）
  - CSV(cp932/utf-8-sig)/JSON 両対応、候補列名の先頭一致、都道府県名→JISコード(全47)、
    住所→説明フォールバック、デフォルト値、`mapping_preset: suishou_kanko`(推奨データセット標準)
  - config/opendata_datasets.json（動作するローカルサンプル + 実データ雛形 enabled:false）
  - map_rows とローカルサンプル取得を単体テスト（+4, 計36 passed）
- 追加: プリセットのみ運用 + 更新機能
  - OPENDATA_PRESET_URLS: 推奨データセットCSVのURLを貼るだけで取り込み（マッピング不要）
  - 更新機能: 定期再収集(COLLECT_INTERVAL_SECONDS)、(source_key,external_id)で差分UPDATE、
    content_hash一致はスキップ、全件スナップショット系(fixtures)は消えた項目を status='hidden'
    にソフト削除、Admin override は locked=true で人手編集を保護
  - collector_runs に updated/pruned 列、Admin画面に表示、SNSは公式APIのみ/他サイトはRSS
  - migration 0008、ext_key/preset/prune を単体テスト（計38 passed）

### Phase 8-9: MVP7 中国語コンテンツ / MVP8 PWA（2026-08-17）
- **MVP7:** content generator(純粋関数, term map翻訳)で小红书/微信/60秒動画台本を生成、
  content_drafts、下書きのみ・自動公開なし・人間レビュー、API /content/*、/content UI。
  tests content_generator 5（backend 計29 passed）
- **MVP8:** manifest.webmanifest + sw.js(オフラインcache)、SVGアイコン、モバイルbottom nav、
  お気に入り/最近見た/保存プラン(localStorage)、共有(Web Share API)、/saved ページ。
  frontend build 成功(9 routes)
- **状態:** MVP0→MVP8 全完了。実行時検証(docker)は未実施(この環境にdaemon無し)

### Phase 7: MVP6 — AI旅行プランナー（2026-08-17）
- **Status:** complete
- planner engine(純粋関数): 制約解析(purpose→tags)/nearest-neighborルート/移動時間・
  予算(交通per-person or 車共有/食事/入場)/スケジュール(08:00起点・昼食挿入)。DBの実データのみ
- backend: /planner/generate（地理検索→候補ランキング→食検索→ルート→予算→保存→検証）、
  /planner/{id}、travel_plans/travel_plan_items（再現可能な入力条件を保存）
- frontend: /planner フォーム＆結果（時刻・費用内訳・各項目の出典リンク）
- テスト: planner_engine 6（計 **24 passed**）。frontend build 成功(7 routes)
- MVP成功条件「大阪発・日帰り・5000円・車なし・魚・絶景 → 根拠付きプラン」を実装で充足
  （実行検証は要 docker; scripts/plan.sh で確認可能）

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| backend health smoke | pytest tests/ | 2 passed | 2 passed | ✓ |
| compose config | docker compose config -q | 検証OK | COMPOSE_OK | ✓ |
| MVP1 routes/validation | pytest tests/ | 4 passed | 4 passed | ✓ |
| DB live query (seed/nearby) | docker compose | 未実施 | この環境は docker daemon 不可 | 保留 |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-08-17 | git push 403 | 1 | Claude GitHub App 未インストール → インストールで解決 |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 2 (MVP1: Database) |
| Where am I going? | MVP1→MVP8 を順に実装 |
| What's the goal? | 関西の実用MVP（根拠付き旅行プラン生成） |
| What have I learned? | See findings.md |
| What have I done? | MVP0 完了・push 済み |

---
*Update after completing each phase or encountering errors*
