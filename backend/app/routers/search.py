"""Simple text search over spots (name / name_en / description)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from geoalchemy2 import Geometry
from sqlalchemy import cast, func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Spot
from app.schemas import SpotOut

router = APIRouter(tags=["search"])

_LAT = func.ST_Y(cast(Spot.location, Geometry))
_LNG = func.ST_X(cast(Spot.location, Geometry))


@router.get("/search", response_model=list[SpotOut])
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[SpotOut]:
    like = f"%{q}%"
    stmt = (
        select(Spot, _LAT, _LNG)
        .where(Spot.status == "published")
        .where(
            or_(
                Spot.name.ilike(like),
                Spot.name_en.ilike(like),
                Spot.description.ilike(like),
            )
        )
        .limit(limit)
    )
    results = []
    for row in db.execute(stmt).all():
        out = SpotOut.model_validate(row[0])
        out.lat = row[1]
        out.lng = row[2]
        results.append(out)
    return results
