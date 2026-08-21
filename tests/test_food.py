"""Restaurant food inference + Overpass restaurant parsing (offline)."""

import os
import sys

COLLECTOR = os.path.join(os.path.dirname(__file__), "..", "collector")
sys.path.insert(0, COLLECTOR)

from food import infer_food  # noqa: E402
from sources import build_sources  # noqa: E402
from sources.overpass_food import parse_restaurants  # noqa: E402


def test_infer_food_sushi_is_fish_and_seafood():
    f = infer_food("sushi;seafood", "海鮮寿司 なんば")
    assert f["fish"] and "寿司" in f["tags"] and "海鮮" in f["tags"]
    assert f["category"] == "sushi"


def test_infer_food_yakiniku_is_meat_local():
    f = infer_food("yakiniku", "焼肉 大阪")
    assert f["meat"] and "肉" in f["tags"]


def test_infer_food_ramen_is_noodles_local():
    f = infer_food("ramen", "和歌山ラーメン")
    assert "麺" in f["tags"] and f["local_specialty"] and f["category"] == "ramen"


def test_infer_food_unknown_defaults():
    f = infer_food(None, "レストラン")
    assert f["category"] == "restaurant"
    assert not any([f["fish"], f["meat"], f["vegetarian"], f["vegan"]])


def test_parse_restaurants_extracts_points():
    els = [
        {"type": "node", "id": 10, "lat": 34.66, "lon": 135.50,
         "tags": {"name": "かに料理", "amenity": "restaurant", "cuisine": "seafood"}},
        {"type": "node", "id": 11, "lat": 34.6, "lon": 135.5, "tags": {"amenity": "restaurant"}},  # no name
    ]
    recs = parse_restaurants(els, "27")
    assert [r.name for r in recs] == ["かに料理"]
    assert recs[0].source_key == "osm_restaurants" and recs[0].prefecture_code == "27"


def test_restaurant_source_registered_as_writer():
    by_key = {s.key: s for s in build_sources()}
    assert "osm_restaurants" in by_key
    assert by_key["osm_restaurants"].writes_restaurants is True
