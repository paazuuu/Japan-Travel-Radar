"""AI travel planner (08). Uses only DB data; every candidate carries a source.

Pipeline: constraint parse -> geospatial search -> candidate ranking ->
food search -> route -> budget -> itinerary -> validation -> persist.
The itinerary math lives in app.planner.engine (pure, tested); this module does
the DB queries and saves the reproducible plan.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import llm
from app.db import get_db
from app.planner import engine
from app.schemas import PlanOut, PlanRequest

router = APIRouter(prefix="/planner", tags=["planner"])

# Named origins (fallback when explicit coords are not given).
ORIGINS = {
    "大阪": (34.7025, 135.4959), "大阪駅": (34.7025, 135.4959), "梅田": (34.7025, 135.4959),
    "京都": (34.9858, 135.7588), "京都駅": (34.9858, 135.7588),
    "神戸": (34.6790, 135.1780), "三宮": (34.6946, 135.1980),
    "奈良": (34.6798, 135.8290), "和歌山": (34.2306, 135.1675),
}

# transport -> day-trip search radius (meters)
RADIUS = {"train": 60000, "car": 90000, "walk": 6000}


def _resolve_origin(req: PlanRequest) -> tuple[float, float]:
    if req.origin_lat is not None and req.origin_lng is not None:
        return req.origin_lat, req.origin_lng
    for key, coord in ORIGINS.items():
        if key in req.origin:
            return coord
    return ORIGINS["大阪"]


def _candidate_spots(db: Session, lat: float, lng: float, radius: int) -> list[dict]:
    rows = db.execute(text("""
        WITH latest AS (SELECT max(score_date) d FROM trend_scores)
        SELECT s.id, s.name,
               ST_Y(s.location::geometry) AS lat, ST_X(s.location::geometry) AS lng,
               COALESCE(s.recommended_stay_minutes, 90) AS stay,
               COALESCE(s.estimated_budget_min, 0) AS entrance,
               COALESCE(t.trend_score, 0) AS trend_score,
               COALESCE(a.tags, '[]'::jsonb) AS tags,
               COALESCE(s.official_url, s.source_url) AS source_url,
               ST_Distance(s.location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS dist
        FROM spots s
        LEFT JOIN spot_analyses a ON a.spot_id = s.id
        LEFT JOIN trend_scores t ON t.spot_id = s.id AND t.score_date = (SELECT d FROM latest)
        WHERE s.status = 'published' AND s.location IS NOT NULL
          AND ST_DWithin(s.location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
        ORDER BY dist ASC
        LIMIT 60
    """), {"lat": lat, "lng": lng, "radius": radius}).mappings().all()
    return [dict(r) for r in rows]


def _pick_restaurant(db: Session, lat: float, lng: float, radius: int, food: str | None) -> dict | None:
    fish_filter = "AND fish = true" if food and ("魚" in food or "fish" in food.lower()) else ""
    row = db.execute(text(f"""
        SELECT id, name, ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
               COALESCE(price_min, 1500) AS price, COALESCE(source_url, official_url) AS source_url
        FROM restaurants
        WHERE location IS NOT NULL
          AND ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
          {fish_filter}
        ORDER BY ST_Distance(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) ASC
        LIMIT 1
    """), {"lat": lat, "lng": lng, "radius": radius}).mappings().first()
    return dict(row) if row else None


@router.post("/generate", response_model=PlanOut)
def generate(req: PlanRequest, db: Session = Depends(get_db)) -> PlanOut:
    origin = _resolve_origin(req)
    radius = RADIUS.get(req.transport, 60000)

    # Constraint parse: purpose -> preferred tags.
    wanted_tags = engine.purpose_to_tags(req.purpose)

    raw = _candidate_spots(db, origin[0], origin[1], radius)
    if not raw:
        raise HTTPException(status_code=404, detail="no spots found near origin (seed data required)")

    # Candidate ranking: tag match first, then trend score.
    def score(c: dict) -> tuple:
        tags = c.get("tags") or []
        match = len(set(tags) & set(wanted_tags))
        return (match, float(c["trend_score"]))

    ranked = sorted(raw, key=score, reverse=True)
    top = ranked[: max(1, min(req.max_spots, 4))]

    candidates = [
        engine.Candidate(
            id=str(c["id"]), name=c["name"], lat=float(c["lat"]), lng=float(c["lng"]),
            stay_min=int(c["stay"]), entrance=int(c["entrance"]),
            trend_score=float(c["trend_score"]), tags=list(c.get("tags") or []),
            source_url=c.get("source_url"),
        )
        for c in top
    ]
    ordered = engine.order_by_nearest(origin, candidates)

    rest_row = _pick_restaurant(db, origin[0], origin[1], radius, req.food)
    restaurant = None
    if rest_row:
        restaurant = engine.Candidate(
            id=str(rest_row["id"]), name=rest_row["name"], lat=float(rest_row["lat"]),
            lng=float(rest_row["lng"]), entrance=int(rest_row["price"]),
            source_url=rest_row.get("source_url"),
        )

    result = engine.build_itinerary(
        origin=origin, origin_name=req.origin, ordered_spots=ordered, restaurant=restaurant,
        transport=req.transport, party_size=req.party_size, budget=req.budget,
    )

    summary = (
        f"{req.origin}発 {'日帰り' if req.days <= 1 else f'{req.days}日'}・"
        f"{req.transport}・予算¥{req.budget or '-'}・{req.purpose or '観光'}。"
        f"候補{len(ordered)}スポット、合計¥{result.total_cost}"
        f"（{'予算内' if result.within_budget else '予算超過'}）。"
    )
    # Optional LLM narrative from the structured plan (facts only; no invention).
    if llm.available():
        nicer = llm.plan_summary({
            "origin": req.origin, "transport": req.transport, "budget": req.budget,
            "purpose": req.purpose, "food": req.food,
            "spots": [c.name for c in ordered],
            "total_cost": result.total_cost, "within_budget": result.within_budget,
        })
        if nicer:
            summary = nicer

    plan_id = _persist(db, req, origin, result, summary)
    return _to_out(db, plan_id)


def _persist(db: Session, req: PlanRequest, origin, result: engine.PlanResult, summary: str) -> str:
    prefs = {"purpose": req.purpose, "food": req.food, "travel_type": req.travel_type}
    pid = db.execute(text("""
        INSERT INTO travel_plans (origin, origin_lat, origin_lng, start_date, days, budget,
                                  party_size, transport, preferences, summary, total_cost, within_budget)
        VALUES (:origin, :lat, :lng, :start_date, :days, :budget, :party, :transport,
                CAST(:prefs AS JSONB), :summary, :total, :within)
        RETURNING id
    """), {
        "origin": req.origin, "lat": origin[0], "lng": origin[1], "start_date": req.start_date,
        "days": req.days, "budget": req.budget, "party": req.party_size, "transport": req.transport,
        "prefs": json.dumps(prefs, ensure_ascii=False), "summary": summary,
        "total": result.total_cost, "within": result.within_budget,
    }).scalar_one()

    for it in result.items:
        db.execute(text("""
            INSERT INTO travel_plan_items (plan_id, sequence, kind, spot_id, restaurant_id,
                                           label, start_time, end_time, estimated_cost, travel_time, source_url)
            VALUES (:plan, :seq, :kind, :spot, :rest, :label, :st, :et, :cost, :tt, :src)
        """), {
            "plan": pid, "seq": it.sequence, "kind": it.kind,
            "spot": it.ref_id if it.kind in ("spot",) else None,
            "rest": it.ref_id if it.kind in ("meal", "cafe") else None,
            "label": it.label, "st": it.start_time, "et": it.end_time,
            "cost": it.estimated_cost, "tt": it.travel_time, "src": it.source_url,
        })
    db.commit()
    return str(pid)


def _to_out(db: Session, plan_id: str) -> PlanOut:
    plan = db.execute(text("SELECT * FROM travel_plans WHERE id = :id"), {"id": plan_id}).mappings().first()
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")
    items = db.execute(text(
        "SELECT sequence, kind, label, start_time, end_time, estimated_cost, travel_time, "
        "spot_id, restaurant_id, source_url FROM travel_plan_items WHERE plan_id = :id ORDER BY sequence"
    ), {"id": plan_id}).mappings().all()
    p = dict(plan)
    return PlanOut(
        id=p["id"], origin=p["origin"], days=p["days"], budget=p["budget"],
        party_size=p["party_size"], transport=p["transport"], summary=p["summary"],
        total_cost=p["total_cost"], within_budget=p["within_budget"],
        items=[dict(i) for i in items],
    )


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: uuid.UUID, db: Session = Depends(get_db)) -> PlanOut:
    return _to_out(db, str(plan_id))
