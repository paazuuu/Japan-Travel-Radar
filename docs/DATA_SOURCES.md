# データソース一覧（Collector）

`12_DATA_GOVERNANCE.md` の原則に従い、**出所の追跡**と**ライセンス確認**を前提に収集する。
「取得できる技術」と「利用してよいデータ」は別物であり、各ソースの規約を守ること。

## 実装済みソース

| source_key | 種別 | Tier | ライセンス / 規約 | 取得方法 | 備考 |
|---|---|---|---|---|---|
| `tourism_opendata` | opendata | 1 | サンプル（要検証） | ローカル fixture | 開発用の代表データ |
| `government_opendata` | opendata | 1 | サンプル（要検証） | ローカル fixture | 同上 |
| `events_official` | events | 1 | サンプル（要検証） | ローカル fixture | 祭・イベント |
| `osm_overpass` | opendata | 2 | **ODbL 1.0**（© OpenStreetMap contributors） | Overpass API | 関西6府県を admin_level=4 で area 指定、座標付きPOI |
| `wikidata` | opendata | 1 | **CC0 1.0**（パブリックドメイン） | SPARQL | 観光地(P31/P279* Q570116) × 府県(P131*) × 座標(P625) |
| `opendata_url` | opendata | 1 | 各データセットの規約 | 設定URL(JSON) | `OPENDATA_JSON_URLS` で自治体等の公開データを差し込み |
| `rss` | rss | 2 | 各媒体の規約（見出し+リンクのみ保存） | RSS | `RSS_FEEDS` |
| `youtube` | youtube | 2 | YouTube Data API 利用規約 | 公式APIのみ | `YOUTUBE_API_KEY`。スクレイプしない |

## ライセンス / 帰属

- **OpenStreetMap (Overpass)**: 表示に「© OpenStreetMap contributors」を明記。ODbL のため
  派生データベースの配布時は条件を確認。各レコードに OSM 要素URLを `source_url` として保存。
- **Wikidata**: CC0。帰属義務はないが、`source_url` に item URL を保存して追跡可能にする。
- **自治体オープンデータ**: 多くは「政府標準利用規約」または CC-BY。利用時は各データセットの
  規約ページを確認し、必要なら帰属を表示。

## 設定（.env）

```env
# ネットワーク収集を止める（fixtureのみ）
COLLECTOR_DISABLE_NETWORK=1

# Overpass / Wikidata エンドポイント（通常は既定でよい）
OVERPASS_URL=https://overpass-api.de/api/interpreter
WIKIDATA_URL=https://query.wikidata.org/sparql

# 自治体等の公開データ（JSON配列を返すURLをカンマ区切り）
# 各要素は fixture と同じ項目: name(必須), lat, lng, prefecture_code,
#   category, subcategory, description, official_url, url, license_note
OPENDATA_JSON_URLS=https://example.jp/spots.json,https://city.example.jp/tourism.json

# RSS / YouTube
RSS_FEEDS=https://example.jp/feed.xml
YOUTUBE_API_KEY=...
```

## 実行

```bash
docker compose up -d --build
./scripts/seed.sh          # 参照データ + 少量seed
./scripts/collect.sh       # 全ソースを1回収集（osm_overpass / wikidata が実データを投入）
./scripts/analyze.sh       # 収集分を含めAI分析
./scripts/rank.sh          # スコア更新
```

`collector_runs` / `collection_errors` は `/api/v1/admin/collector-runs`・`/admin/errors`
または Admin 画面で確認できる。重複は content_hash / 公式URL / 名称+座標距離で抑制される。

## 注意（この開発環境について）

CI/サンドボックスによっては egress ポリシーで Overpass/Wikidata 等が 403 になる場合がある。
その場合ネットワークソースは自動的に degrade（`collection_errors` に記録）し、fixture ソース
だけで日次ジョブは成功する。実データ取得は通常の Docker 実行環境（外部到達可）で行うこと。
