"""Event endpoints (first-class events table)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import EventOut

router = APIRouter(prefix="/events", tags=["events"])

_SELECT = """
    SELECT id, name, description, category, subcategory, prefecture_id,
           ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
           to_char(start_at, 'YYYY-MM-DD') AS start_at,
           to_char(end_at, 'YYYY-MM-DD') AS end_at,
           official_url, image_url, source_url
    FROM events
    WHERE COALESCE(status, 'published') = 'published'
"""


def _rows(db: Session, sql: str, params: dict) -> list[EventOut]:
    result = db.execute(text(sql), params).mappings().all()
    return [EventOut(**dict(r)) for r in result]


@router.get("", response_model=list[EventOut])
def list_events(
    db: Session = Depends(get_db),
    prefecture_id: str | None = Query(default=None),
    upcoming: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EventOut]:
    sql = _SELECT
    params: dict = {"limit": limit}
    if prefecture_id:
        sql += " AND prefecture_id = :pref"
        params["pref"] = prefecture_id
    if upcoming:
        sql += " AND (end_at IS NULL OR end_at >= now())"
    sql += " ORDER BY start_at NULLS LAST LIMIT :limit"
    return _rows(db, sql, params)


@router.get("/upcoming", response_model=list[EventOut])
def upcoming_events(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> list[EventOut]:
    sql = _SELECT + " AND (end_at IS NULL OR end_at >= now()) ORDER BY start_at NULLS LAST LIMIT :limit"
    return _rows(db, sql, {"limit": limit})


@router.get("/nearby", response_model=list[EventOut])
def nearby_events(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: int = Query(default=30000, ge=1, le=200000),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[EventOut]:
    sql = _SELECT + (
        " AND location IS NOT NULL"
        " AND ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)"
        " ORDER BY ST_Distance(location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) LIMIT :limit"
    )
    return _rows(db, sql, {"lat": lat, "lng": lng, "radius": radius, "limit": limit})
