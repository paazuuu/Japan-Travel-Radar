"""Spot endpoints: list, detail, nearby, search."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2 import Geography, Geometry
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Spot
from app.schemas import SpotOut

router = APIRouter(prefix="/spots", tags=["spots"])

# geography -> geometry cast lets us read lon/lat with ST_X / ST_Y.
_LAT = func.ST_Y(cast(Spot.location, Geometry))
_LNG = func.ST_X(cast(Spot.location, Geometry))


def _geog_point(lat: float, lng: float):
    """Build a geography POINT for ST_DWithin / ST_Distance (meters)."""
    return cast(func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326), Geography)


def _row_to_out(row) -> SpotOut:
    spot: Spot = row[0]
    out = SpotOut.model_validate(spot)
    out.lat = row[1]
    out.lng = row[2]
    if len(row) > 3:
        out.distance_m = row[3]
    return out


@router.get("", response_model=list[SpotOut])
def list_spots(
    db: Session = Depends(get_db),
    category: str | None = Query(default=None),
    prefecture_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[SpotOut]:
    stmt = select(Spot, _LAT, _LNG).where(Spot.status == "published")
    if category:
        stmt = stmt.where(Spot.category == category)
    if prefecture_id:
        stmt = stmt.where(Spot.prefecture_id == prefecture_id)
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
        select(Spot, _LAT, _LNG, distance.label("distance_m"))
        .where(Spot.status == "published")
        .where(Spot.location.isnot(None))
        .where(func.ST_DWithin(Spot.location, point, radius))
        .order_by(distance.asc())
        .limit(limit)
    )
    return [_row_to_out(r) for r in db.execute(stmt).all()]


@router.get("/{spot_id}", response_model=SpotOut)
def get_spot(spot_id: uuid.UUID, db: Session = Depends(get_db)) -> SpotOut:
    stmt = select(Spot, _LAT, _LNG).where(Spot.id == spot_id)
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=404, detail="spot not found")
    return _row_to_out(row)
