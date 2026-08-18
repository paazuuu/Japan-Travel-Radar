"""Restaurant endpoints: list, detail, nearby (with food-attribute filters)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2 import Geography, Geometry
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Restaurant
from app.schemas import RestaurantOut

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

_LAT = func.ST_Y(cast(Restaurant.location, Geometry))
_LNG = func.ST_X(cast(Restaurant.location, Geometry))


def _geog_point(lat: float, lng: float):
    return cast(func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326), Geography)


def _row_to_out(row) -> RestaurantOut:
    r: Restaurant = row[0]
    out = RestaurantOut.model_validate(r)
    out.lat = row[1]
    out.lng = row[2]
    if len(row) > 3:
        out.distance_m = row[3]
    return out


@router.get("", response_model=list[RestaurantOut])
def list_restaurants(
    db: Session = Depends(get_db),
    category: str | None = Query(default=None),
    fish: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[RestaurantOut]:
    stmt = select(Restaurant, _LAT, _LNG)
    if category:
        stmt = stmt.where(Restaurant.category == category)
    if fish is not None:
        stmt = stmt.where(Restaurant.fish.is_(fish))
    stmt = stmt.order_by(Restaurant.updated_at.desc()).limit(limit).offset(offset)
    return [_row_to_out(r) for r in db.execute(stmt).all()]


@router.get("/nearby", response_model=list[RestaurantOut])
def nearby_restaurants(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: int = Query(default=3000, ge=1, le=100000, description="meters"),
    fish: bool | None = Query(default=None),
    local_specialty: bool | None = Query(default=None),
    max_price: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[RestaurantOut]:
    point = _geog_point(lat, lng)
    distance = func.ST_Distance(Restaurant.location, point)
    stmt = (
        select(Restaurant, _LAT, _LNG, distance.label("distance_m"))
        .where(Restaurant.location.isnot(None))
        .where(func.ST_DWithin(Restaurant.location, point, radius))
    )
    if fish is not None:
        stmt = stmt.where(Restaurant.fish.is_(fish))
    if local_specialty is not None:
        stmt = stmt.where(Restaurant.local_specialty.is_(local_specialty))
    if max_price is not None:
        stmt = stmt.where(Restaurant.price_min <= max_price)
    stmt = stmt.order_by(distance.asc()).limit(limit)
    return [_row_to_out(r) for r in db.execute(stmt).all()]


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id: uuid.UUID, db: Session = Depends(get_db)) -> RestaurantOut:
    stmt = select(Restaurant, _LAT, _LNG).where(Restaurant.id == restaurant_id)
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=404, detail="restaurant not found")
    return _row_to_out(row)
