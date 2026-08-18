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
| `opendata_datasets` | opendata | 1 | 各データセットの規約 | 設定ファイル(CSV/JSON+列マッピング) | `config/opendata_datasets.json`。列名マッピングで実データを取り込み。サンプルCSV同梱 |
| `opendata_url` | opendata | 1 | 各データセットの規約 | 設定URL(JSON) | `OPENDATA_JSON_URLS`。fixtureと同じ項目名のJSON配列をそのまま取り込み |
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

## 自治体オープンデータの追加（列名マッピング）

実データは CSV（Shift_JIS/cp932 も可）や独自の日本語列名で提供されることが多い。
`collector/config/opendata_datasets.json` にデータセット記述を追加するだけで、
**コード変更なし**で取り込める（`opendata_datasets` ソース）。

### データセット記述の例

```jsonc
{
  "key": "osaka_kanko",
  "name": "大阪府 観光施設オープンデータ",
  "enabled": true,
  "url": "https://<配布元で確認した資源URL>.csv",  // ローカル検証は "path": "data/xxx.csv"
  "format": "csv",              // csv | json
  "encoding": "cp932",          // Shift_JIS は cp932 / utf-8-sig など
  "license_note": "CC BY 4.0（配布元で要確認）",
  "mapping_preset": "suishou_kanko",   // 「推奨データセット（観光施設一覧）」標準列に対応
  "mapping": {                          // 追加/上書き。候補列名の先頭一致で採用
    "name": ["名称", "施設名"],
    "lat": ["緯度"], "lng": ["経度"],
    "description": ["説明", "概要"],
    "official_url": ["URL"],
    "prefecture_name": ["都道府県名"],  // 名称→JISコードに自動変換（全47対応）
    "category": ["カテゴリ", "分類"]
  },
  "defaults": { "prefecture_code": "27", "category": "sightseeing" }
}
```

- `mapping_preset: "suishou_kanko"` はデジタル庁「推奨データセット（観光施設一覧）」の
  標準列名（都道府県名/名称/緯度/経度/説明/URL/住所…）に対応。準拠CSVならURLを足すだけ。
- `prefecture_name` 列があれば「大阪府」→ `27` のように**都道府県コードへ自動変換**。
  無ければ `defaults.prefecture_code` を使用。
- 住所しか無い場合は住所を説明にフォールバック。名称が無い行はスキップ。
- 既定の設定ファイルには**動作するローカルサンプル**（`data/sample_kanko.csv`, enabled）と、
  実データ用の雛形（enabled:false, URLを確認して有効化）を同梱。
- `map_rows` はオフライン単体テスト済み（`tests/test_datasets_mapping.py`）。

### 追加手順

1. 対象データセットの**資源URL**と**列名**・**文字コード**・**ライセンス**を配布元で確認。
2. `collector/config/opendata_datasets.json` に記述を追加し `enabled: true`。
3. `./scripts/collect.sh` を実行（`opendata_datasets` が取り込み、重複は自動抑制）。

> 別ファイルで管理したい場合は `.env` の `OPENDATA_CONFIG=/path/to/your.json` を指定。

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
