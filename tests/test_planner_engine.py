"""MVP6: planner engine unit tests (no DB / no LLM)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/none")

from app.planner import engine  # noqa: E402


def test_travel_time_and_cost_scale_with_transport():
    d = 45000  # 45 km straight line
    assert engine.travel_time_min(d, "walk") > engine.travel_time_min(d, "train")
    assert engine.leg_cost(d, "walk", 2) == 0
    # train cost is per-person
    assert engine.leg_cost(d, "train", 2) == 2 * engine.leg_cost(d, "train", 1)


def test_order_by_nearest():
    origin = (34.70, 135.50)
    cands = [
        engine.Candidate("a", "far", 35.5, 136.5),
        engine.Candidate("b", "near", 34.71, 135.51),
        engine.Candidate("c", "mid", 34.9, 135.7),
    ]
    ordered = engine.order_by_nearest(origin, cands)
    assert [c.name for c in ordered] == ["near", "mid", "far"]


def test_purpose_to_tags():
    assert "絶景" in engine.purpose_to_tags("絶景が見たい")
    assert engine.purpose_to_tags(None) == []


def test_build_itinerary_budget_and_schedule():
    origin = (34.7025, 135.4959)
    spots = [
        engine.Candidate("s1", "城", 34.687, 135.526, stay_min=90, entrance=600, source_url="http://a"),
        engine.Candidate("s2", "寺", 34.995, 135.785, stay_min=60, entrance=400, source_url="http://b"),
    ]
    restaurant = engine.Candidate("r1", "海鮮", 34.67, 135.50, entrance=2000, source_url="http://r")
    res = engine.build_itinerary(
        origin=origin, origin_name="大阪", ordered_spots=spots, restaurant=restaurant,
        transport="train", party_size=2, budget=20000,
    )
    kinds = [i.kind for i in res.items]
    assert kinds[0] == "depart" and kinds[-1] == "return"
    assert "spot" in kinds and "meal" in kinds
    # cost accounting adds up
    assert res.total_cost == res.transport_cost + res.food_cost + res.entrance_cost
    assert res.entrance_cost == (600 + 400) * 2
    assert res.food_cost == 2000 * 2
    assert res.within_budget is True
    # times are ordered strings HH:MM
    assert res.items[0].start_time == "08:00"


def test_over_budget_flagged():
    origin = (34.70, 135.50)
    spots = [engine.Candidate("s1", "x", 35.5, 136.6, entrance=9000)]
    res = engine.build_itinerary(
        origin=origin, origin_name="大阪", ordered_spots=spots, restaurant=None,
        transport="train", party_size=2, budget=1000,
    )
    assert res.within_budget is False
