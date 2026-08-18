"""Real-data source parsers: Overpass + Wikidata (offline, no network).

Validates parsing against real-shaped API payloads and that the registry
includes the new sources. Live fetching runs in the docker deployment.
"""

import os
import sys

COLLECTOR = os.path.join(os.path.dirname(__file__), "..", "collector")
sys.path.insert(0, COLLECTOR)

from sources import build_sources  # noqa: E402
from sources.overpass import parse_elements  # noqa: E402
from sources.wikidata import parse_bindings  # noqa: E402


OVERPASS_SAMPLE = {
    "elements": [
        {"type": "node", "id": 1, "lat": 34.6873, "lon": 135.5259,
         "tags": {"name": "大阪城", "historic": "castle", "website": "https://osakacastle.net"}},
        {"type": "way", "id": 2, "center": {"lat": 34.6851, "lon": 135.843},
         "tags": {"name": "奈良公園", "leisure": "park"}},
        {"type": "node", "id": 3, "lat": 34.9, "lon": 135.7, "tags": {"tourism": "museum", "name": "博物館"}},
        {"type": "node", "id": 4, "lat": 34.9, "lon": 135.7, "tags": {"historic": "castle"}},  # no name -> skipped
        {"type": "node", "id": 5, "tags": {"name": "座標なし"}},  # no coords -> skipped
    ]
}

WIKIDATA_SAMPLE = [
    {"item": {"value": "http://www.wikidata.org/entity/Q182022"},
     "itemLabel": {"value": "清水寺"},
     "lat": {"value": "34.9948"}, "lon": {"value": "135.785"},
     "prefLabel": {"value": "京都府"}},
    {"item": {"value": "http://www.wikidata.org/entity/Q999"},
     "itemLabel": {"value": "圏外"},
     "lat": {"value": "35.0"}, "lon": {"value": "135.0"},
     "prefLabel": {"value": "東京都"}},  # not Kansai -> skipped
]


def test_overpass_parse_maps_category_and_skips_bad_rows():
    recs = parse_elements(OVERPASS_SAMPLE["elements"], "27")
    names = [r.name for r in recs]
    assert names == ["大阪城", "奈良公園", "博物館"]
    castle = next(r for r in recs if r.name == "大阪城")
    assert castle.category == "sightseeing" and castle.subcategory == "castle"
    assert castle.prefecture_code == "27"
    assert castle.external_id == "node/1"
    assert "ODbL" in (castle.license_note or "")
    park = next(r for r in recs if r.name == "奈良公園")
    assert park.category == "nature" and (park.lat, park.lng) == (34.6851, 135.843)


def test_wikidata_parse_filters_to_kansai_and_maps_pref():
    recs = parse_bindings(WIKIDATA_SAMPLE)
    assert len(recs) == 1
    r = recs[0]
    assert r.name == "清水寺" and r.prefecture_code == "26"
    assert r.external_id == "Q182022"
    assert "CC0" in (r.license_note or "")


def test_registry_includes_real_sources():
    keys = {s.key for s in build_sources()}
    assert {"osm_overpass", "wikidata", "opendata_url"} <= keys
    assert len(keys) >= 7
