"""Configured open-data column mapping (offline; uses the bundled sample CSV)."""

import os
import sys

COLLECTOR = os.path.join(os.path.dirname(__file__), "..", "collector")
sys.path.insert(0, COLLECTOR)

from sources.datasets import (  # noqa: E402
    ConfiguredDatasetsSource,
    DatasetSpec,
    build_spec,
    map_rows,
)


def test_suishou_preset_maps_standard_columns():
    spec = build_spec({
        "key": "t", "name": "t", "mapping_preset": "suishou_kanko",
        "defaults": {"category": "sightseeing"},
    })
    rows = [
        {"都道府県名": "京都府", "名称": "錦市場", "緯度": "35.0050", "経度": "135.7649", "説明": "京の台所"},
        {"都道府県名": "大阪府", "名称": "新世界", "緯度": "34.6520", "経度": "135.5063", "住所": "浪速区"},
        {"都道府県名": "兵庫県", "名称": "", "緯度": "1", "経度": "1"},  # no name -> skipped
    ]
    recs = map_rows(rows, spec)
    assert [r.name for r in recs] == ["錦市場", "新世界"]
    nishiki = recs[0]
    assert nishiki.prefecture_code == "26"        # 京都府 -> 26
    assert (nishiki.lat, nishiki.lng) == (35.0050, 135.7649)
    assert nishiki.category == "sightseeing"      # from defaults
    # address used as description fallback
    assert recs[1].description == "浪速区"


def test_custom_mapping_and_default_prefecture_code():
    spec = build_spec({
        "key": "c", "name": "c",
        "mapping": {"name": ["spot_name"], "lat": ["latitude"], "lng": ["longitude"],
                    "official_url": ["url"]},
        "defaults": {"prefecture_code": "27", "category": "gourmet"},
    })
    rows = [{"spot_name": "テスト", "latitude": "34.7", "longitude": "135.5", "url": "http://x"}]
    r = map_rows(rows, spec)[0]
    assert r.prefecture_code == "27" and r.category == "gourmet"
    assert r.official_url == "http://x" and r.lat == 34.7


def test_bundled_sample_csv_fetches_offline():
    # The default config's sample dataset uses a local path -> works without network.
    src = ConfiguredDatasetsSource()
    recs = src.fetch()
    names = {r.name for r in recs}
    assert {"錦市場", "新世界", "北野異人館街", "八幡堀"} <= names
    kobe = next(r for r in recs if r.name == "北野異人館街")
    assert kobe.prefecture_code == "28"           # 兵庫県 -> 28
    assert kobe.lat and kobe.lng
    assert src.errors == []                         # local read has no errors


def test_disabled_examples_are_not_fetched():
    # Only the enabled sample runs; the disabled real-dataset templates are skipped.
    src = ConfiguredDatasetsSource()
    keys = {r.source_key for r in src.fetch()}
    assert keys == {"sample_suishou_kanko"}
