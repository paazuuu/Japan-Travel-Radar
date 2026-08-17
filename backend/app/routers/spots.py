"""Spot endpoints: list, detail, nearby, search — enriched with AI analysis."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2 import Geography, Geometry
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Spot, SpotAnalysis
from app.schemas import AnalysisOut, SpotOut

router = APIRouter(prefix="/spots", tags=["spots"])

_LAT = func.ST_Y(cast(Spot.location, Geometry))
_LNG = func.ST_X(cast(Spot.location, Geometry))

# columns selected alongside the Spot entity (keep index mapping in one place)
_A = SpotAnalysis


def _geog_point(lat: float, lng: float):
    return cast(func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326), Geography)


def _base_select(*extra):
    return (
        select(Spot, _LAT, _LNG, _A.summary, _A.tags, _A.travel_types, _A.confidence, *extra)
        .outerjoin(_A, _A.spot_id == Spot.id)
    )


def _row_to_out(row, with_distance: bool = False) -> SpotOut:
    spot: Spot = row[0]
    out = SpotOut.model_validate(spot)
    out.lat, out.lng = row[1], row[2]
    out.ai_summary = row[3]
    out.tags = list(row[4]) if row[4] else []
    out.travel_types = list(row[5]) if row[5] else []
    out.ai_confidence = float(row[6]) if row[6] is not None else None
    if with_distance:
        out.distance_m = row[7]
    return out


@router.get("", response_model=list[SpotOut])
def list_spots(
    db: Session = Depends(get_db),
    category: str | None = Query(default=None),
    prefecture_id: uuid.UUID | None = Query(default=None),
    tag: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[SpotOut]:
    stmt = _base_select().where(Spot.status == "published")
    if category:
        stmt = stmt.where(Spot.category == category)
    if prefecture_id:
        stmt = stmt.where(Spot.prefecture_id == prefecture_id)
    if tag:
        stmt = stmt.where(_A.tags.contains([tag]))
    stmt = stmt.order_by(Spot.updated_at.desc()).limit(limit).offset(offset)
    return [_row_to_out(r) for r in db.execute(stmt).all()]


@router.get("/nearby", response_model=list[SpotOut])
def nearby_spots(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: int = Query(default=5000, ge=1, le=100000, description="meters"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[SpotOut]:
    point = _geog_point(lat, lng)
    distance = func.ST_Distance(Spot.location, point)
    stmt = (
        _base_select(distance.label("distance_m"))
        .where(Spot.status == "published")
        .where(Spot.location.isnot(None))
        .where(func.ST_DWithin(Spot.location, point, radius))
        .order_by(distance.asc())
        .limit(limit)
    )
    return [_row_to_out(r, with_distance=True) for r in db.execute(stmt).all()]


@router.get("/{spot_id}", response_model=SpotOut)
def get_spot(spot_id: uuid.UUID, db: Session = Depends(get_db)) -> SpotOut:
    row = db.execute(_base_select().where(Spot.id == spot_id)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="spot not found")
    return _row_to_out(row)


@router.get("/{spot_id}/analysis", response_model=AnalysisOut)
def get_spot_analysis(spot_id: uuid.UUID, db: Session = Depends(get_db)) -> AnalysisOut:
    analysis = db.execute(select(_A).where(_A.spot_id == spot_id)).scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="analysis not found")
    return AnalysisOut.model_validate(analysis)
