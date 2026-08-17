"""MVP4: Trend Score unit tests (no DB)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))

from scorer import (  # noqa: E402
    WEIGHTS,
    compute,
    growth_score,
    seasonality_score,
    source_diversity_score,
)


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_growth_ratio_mapping():
    assert growth_score(200, 100)[0] == 100.0   # doubled -> 100
    assert growth_score(100, 100)[0] == 50.0    # flat -> 50
    assert growth_score(None, None) == (50.0, False)  # no data -> neutral, flagged


def test_seasonality_active_vs_off():
    assert seasonality_score(["autumn"], 10) == 100.0   # October in autumn
    assert seasonality_score(["autumn"], 7) == 20.0     # July not autumn/adjacent
    assert seasonality_score([], 7) == 40.0             # unknown -> neutral


def test_source_diversity_scale():
    assert source_diversity_score(1) == 30.0
    assert source_diversity_score(4) == 100.0


def test_compute_flags_reference_when_thin():
    b = compute({"month": 10, "source_count": 1, "confidence": 0.9,
                 "best_seasons": ["autumn"], "sample_size": 0,
                 "updated_days_ago": 1, "created_days_ago": 1})
    assert 0 <= b.trend_score <= 100
    assert b.is_reference is True   # single source + no growth data

    b2 = compute({"month": 10, "source_count": 3, "confidence": 0.9,
                  "best_seasons": ["autumn"], "sample_size": 5,
                  "current_metric": 200, "previous_metric": 100,
                  "updated_days_ago": 1, "created_days_ago": 1})
    assert b2.is_reference is False
    assert b2.growth_score == 100.0
