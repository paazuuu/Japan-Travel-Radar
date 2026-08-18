"""Deterministic planner engine (08_MVP6_TRAVEL_PLANNER.md).

Pure functions only — no DB, no LLM — so the itinerary math (travel time, cost,
route order, schedule) is fully unit-testable. The router supplies DB candidates;
this module never invents places (08: DBに存在しない場所の追加は禁止).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# transport -> (km/h, yen per km, cost_is_per_person)
TRANSPORT = {
    "train": (45.0, 22.0, True),
    "car": (50.0, 18.0, False),   # fuel + rough toll, shared by the party
    "walk": (4.5, 0.0, False),
}
DETOUR = 1.3          # straight-line -> real path factor
DEFAULT_STAY_MIN = 90


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def travel_time_min(distance_m: float, transport: str) -> int:
    speed, _, _ = TRANSPORT.get(transport, TRANSPORT["train"])
    km = distance_m / 1000.0 * DETOUR
    return int(round(km / speed * 60.0))


def leg_cost(distance_m: float, transport: str, party_size: int) -> int:
    speed, per_km, per_person = TRANSPORT.get(transport, TRANSPORT["train"])
    km = distance_m / 1000.0 * DETOUR
    cost = km * per_km
    if per_person:
        cost *= party_size
    return int(round(cost))


@dataclass
class Candidate:
    id: str
    name: str
    lat: float
    lng: float
    stay_min: int = DEFAULT_STAY_MIN
    entrance: int = 0            # per person
    trend_score: float = 0.0
    tags: list[str] = field(default_factory=list)
    source_url: str | None = None


def order_by_nearest(origin: tuple[float, float], candidates: list[Candidate]) -> list[Candidate]:
    """Nearest-neighbour ordering starting from the origin (greedy)."""
    remaining = list(candidates)
    ordered: list[Candidate] = []
    cur = origin
    while remaining:
        nxt = min(remaining, key=lambda c: haversine_m(cur[0], cur[1], c.lat, c.lng))
        ordered.append(nxt)
        remaining.remove(nxt)
        cur = (nxt.lat, nxt.lng)
    return ordered


def _add_minutes(hhmm: str, minutes: int) -> str:
    h, m = map(int, hhmm.split(":"))
    total = h * 60 + m + minutes
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


@dataclass
class PlanItem:
    sequence: int
    kind: str
    label: str
    start_time: str
    end_time: str
    estimated_cost: int
    travel_time: int
    ref_id: str | None = None
    source_url: str | None = None


@dataclass
class PlanResult:
    items: list[PlanItem]
    transport_cost: int
    food_cost: int
    entrance_cost: int
    total_cost: int
    within_budget: bool


def build_itinerary(
    *,
    origin: tuple[float, float],
    origin_name: str,
    ordered_spots: list[Candidate],
    restaurant: Candidate | None,
    transport: str,
    party_size: int,
    budget: int | None,
    start_time: str = "08:00",
) -> PlanResult:
    """Assemble a single-day itinerary with times, legs, and a budget breakdown."""
    items: list[PlanItem] = []
    seq = 0
    transport_cost = food_cost = entrance_cost = 0
    clock = start_time
    cur = origin

    items.append(PlanItem(seq, "depart", f"{origin_name} 出発", clock, clock, 0, 0))
    seq += 1

    lunch_inserted = False

    def insert_lunch(seq_i: int, clk: str, position: tuple[float, float]):
        nonlocal transport_cost, food_cost
        rdist = haversine_m(position[0], position[1], restaurant.lat, restaurant.lng)
        rtmin = travel_time_min(rdist, transport)
        transport_cost += leg_cost(rdist, transport, party_size)
        meal_start = _add_minutes(clk, rtmin)
        meal_end = _add_minutes(meal_start, 60)
        mcost = restaurant.entrance * party_size  # `entrance` carries the meal price for restaurants
        food_cost += mcost
        items.append(PlanItem(seq_i, "meal", f"昼食: {restaurant.name}", meal_start, meal_end,
                              mcost, rtmin, restaurant.id, restaurant.source_url))
        return meal_end, (restaurant.lat, restaurant.lng)

    for spot in ordered_spots:
        # Insert lunch around midday, before heading to the next spot.
        if restaurant and not lunch_inserted and clock >= "11:30":
            clock, cur = insert_lunch(seq, clock, cur)
            seq += 1
            lunch_inserted = True

        dist = haversine_m(cur[0], cur[1], spot.lat, spot.lng)
        tmin = travel_time_min(dist, transport)
        transport_cost += leg_cost(dist, transport, party_size)
        arrive = _add_minutes(clock, tmin)
        depart_spot = _add_minutes(arrive, spot.stay_min)
        ecost = spot.entrance * party_size
        entrance_cost += ecost
        items.append(PlanItem(seq, "spot", f"観光: {spot.name}", arrive, depart_spot,
                              ecost, tmin, spot.id, spot.source_url))
        seq += 1
        clock = depart_spot
        cur = (spot.lat, spot.lng)

    # Fallback: ensure a meal is included when a restaurant is available.
    if restaurant and not lunch_inserted:
        clock, cur = insert_lunch(seq, clock, cur)
        seq += 1
        lunch_inserted = True

    # Return leg to origin.
    dist = haversine_m(cur[0], cur[1], origin[0], origin[1])
    tmin = travel_time_min(dist, transport)
    tcost = leg_cost(dist, transport, party_size)
    transport_cost += tcost
    ret = _add_minutes(clock, tmin)
    items.append(PlanItem(seq, "return", f"{origin_name} 着", ret, ret, 0, tmin))

    total = transport_cost + food_cost + entrance_cost
    within = budget is None or total <= budget
    return PlanResult(items, transport_cost, food_cost, entrance_cost, total, within)


# Purpose keyword -> preferred spot tags (08 example: 絶景, 写真映え ...)
PURPOSE_TAGS = {
    "絶景": ["絶景", "夜景", "海", "山"],
    "景色": ["絶景", "夜景"],
    "写真": ["写真映え", "絶景"],
    "歴史": ["歴史", "文化"],
    "自然": ["自然", "海", "山"],
    "温泉": ["温泉"],
    "家族": ["家族向け"],
    "デート": ["夜景", "写真映え"],
}


def purpose_to_tags(purpose: str | None) -> list[str]:
    if not purpose:
        return []
    tags: list[str] = []
    for key, mapped in PURPOSE_TAGS.items():
        if key in purpose:
            tags.extend(mapped)
    return list(dict.fromkeys(tags))
