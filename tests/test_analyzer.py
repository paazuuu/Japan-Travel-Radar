"""MVP3: rule-based analyzer unit tests (no DB / no network)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))

from analyzer import MODEL_ID, analyze  # noqa: E402


def test_castle_is_history_sightseeing():
    r = analyze("大阪城", "大阪のシンボル。天守閣と公園。", "sightseeing")
    assert "歴史" in r.tags
    assert "sightseeing" in r.categories
    assert r.confidence > 0.5
    assert r.model == MODEL_ID


def test_onsen_winter_and_food_signal():
    r = analyze("有馬温泉", "日本三古湯のひとつ。", "onsen")
    assert "温泉" in r.tags
    assert "winter" in r.best_season
    assert "onsen" in r.categories


def test_aquarium_is_family():
    r = analyze("海遊館", "世界最大級の水族館。", "sightseeing")
    assert "family" in r.travel_types
    assert "家族向け" in r.tags


def test_no_signal_is_low_confidence_not_fabricated():
    r = analyze("XYZ", None, None)
    assert r.confidence <= 0.3
    assert r.tags == []
    assert "weak guess" in r.evidence


def test_structured_output_shape():
    r = analyze("嵐山 竹林の小径", "紅葉の名所。", "nature").to_dict()
    for key in ["summary", "categories", "tags", "best_season",
                "travel_types", "food_tags", "confidence"]:
        assert key in r
