"""Trend Score computation (06_MVP4_RANKING.md).

Trend Score = 0.25*growth + 0.20*engagement + 0.15*recency + 0.15*seasonality
            + 0.10*source_diversity + 0.10*novelty + 0.05*data_confidence

Every component is normalized to 0..100. Pure and deterministic so it is unit
-testable; the worker supplies raw features pulled from the database.
"""

from __future__ import annotations

from dataclasses import dataclass

WEIGHTS = {
    "growth": 0.25,
    "engagement": 0.20,
    "recency": 0.15,
    "seasonality": 0.15,
    "source_diversity": 0.10,
    "novelty": 0.10,
    "data_confidence": 0.05,
}

MIN_SAMPLE = 2  # below this, growth is a "reference value" (06: サンプル数不足)

# month -> seasons active that month
_SEASON_MONTHS = {
    "spring": {3, 4, 5},
    "summer": {6, 7, 8},
    "autumn": {9, 10, 11},
    "winter": {12, 1, 2},
}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def growth_score(current: float | None, previous: float | None) -> tuple[float, bool]:
    """Return (score, has_data). ratio 0.5->0, 1.0->50, 2.0->100 (clamped)."""
    if not current or not previous or previous <= 0:
        return 50.0, False  # neutral, flagged as no-data by caller
    ratio = current / previous
    # ratio 0->0, 1.0->50 (flat), 2.0->100 (doubled), capped.
    score = 50.0 + (ratio - 1.0) * 50.0 if ratio >= 1.0 else ratio * 50.0
    return _clamp(score), True


def engagement_score(count: float) -> float:
    # saturating: 0->0, 50->50, large->~100
    if count <= 0:
        return 0.0
    return _clamp(100.0 * count / (count + 50.0))


def recency_score(updated_days_ago: float) -> float:
    return _clamp(100.0 - updated_days_ago * 2.0)  # ~0 after 50 days


def seasonality_score(best_seasons: list[str], month: int) -> float:
    if not best_seasons:
        return 40.0  # neutral when unknown
    if "all" in best_seasons:
        return 70.0
    active = any(month in _SEASON_MONTHS.get(s, set()) for s in best_seasons)
    if active:
        return 100.0
    # adjacent month bonus
    adj_months = {(month % 12) + 1, (month - 2) % 12 + 1}
    adjacent = any(adj_months & _SEASON_MONTHS.get(s, set()) for s in best_seasons)
    return 60.0 if adjacent else 20.0


def source_diversity_score(source_count: int) -> float:
    return _clamp(30.0 * source_count)  # 1->30, 2->60, 3->90, 4+->100


def novelty_score(created_days_ago: float) -> float:
    return _clamp(100.0 - created_days_ago * (100.0 / 60.0))  # 0 after 60 days


@dataclass
class ScoreBreakdown:
    trend_score: float
    growth_score: float
    engagement_score: float
    recency_score: float
    seasonality_score: float
    source_diversity_score: float
    novelty_score: float
    data_confidence_score: float
    sample_size: int
    is_reference: bool


def compute(features: dict) -> ScoreBreakdown:
    g, g_has = growth_score(features.get("current_metric"), features.get("previous_metric"))
    comp = {
        "growth": g,
        "engagement": engagement_score(features.get("engagement_count", 0) or 0),
        "recency": recency_score(features.get("updated_days_ago", 999) or 999),
        "seasonality": seasonality_score(features.get("best_seasons") or [], features.get("month", 1)),
        "source_diversity": source_diversity_score(features.get("source_count", 1) or 1),
        "novelty": novelty_score(features.get("created_days_ago", 999) or 999),
        "data_confidence": _clamp((features.get("confidence", 0) or 0) * 100.0),
    }
    trend = round(sum(WEIGHTS[k] * comp[k] for k in WEIGHTS), 2)
    sample = int(features.get("sample_size", 0) or 0)
    is_reference = (sample < MIN_SAMPLE) or (not g_has) or ((features.get("source_count", 1) or 1) < 2)

    return ScoreBreakdown(
        trend_score=trend,
        growth_score=round(comp["growth"], 2),
        engagement_score=round(comp["engagement"], 2),
        recency_score=round(comp["recency"], 2),
        seasonality_score=round(comp["seasonality"], 2),
        source_diversity_score=round(comp["source_diversity"], 2),
        novelty_score=round(comp["novelty"], 2),
        data_confidence_score=round(comp["data_confidence"], 2),
        sample_size=sample,
        is_reference=is_reference,
    )
