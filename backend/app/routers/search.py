"""Typo-tolerant, relevance-ranked search over spots.

Upgrades the former naive substring match to use the pg_trgm trigram
similarity already enabled in the DB (GIN index `idx_spots_name_trgm`),
so queries tolerate typos/partial kana and results are ordered by relevance.
Matching spans name / name_en / description and the AI-analysis tags.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Spot
from app.models import SpotAnalysis as _A
from app.routers.spots import _base_select, _row_to_out
from app.schemas import SpotOut

router = APIRouter(tags=["search"])

# trigram similarity floor for a fuzzy name hit (lower = more tolerant recall)
_SIM_THRESHOLD = 0.2


@router.get("/search", response_model=list[SpotOut])
def search(
    q: str = Query(..., min_length=1),
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[SpotOut]:
    like = f"%{q}%"
    # relevance = trigram similarity, boosted by a direct substring hit and an
    # exact AI-tag membership hit so those rank above a loose fuzzy match.
    sim = func.greatest(
        func.similarity(Spot.name, q),
        func.similarity(func.coalesce(Spot.name_en, ""), q),
    )
    relevance = (
        sim
        + case((Spot.name.ilike(like), 0.3), else_=0.0)
        + case((_A.tags.has_key(q), 0.4), else_=0.0)
    ).label("relevance")

    stmt = (
        _base_select(relevance)
        .where(Spot.status == "published")
        .where(
            or_(
                func.similarity(Spot.name, q) > _SIM_THRESHOLD,  # typo tolerant
                Spot.name.ilike(like),
                func.coalesce(Spot.name_en, "").ilike(like),
                func.coalesce(Spot.description, "").ilike(like),
                _A.tags.has_key(q),  # exact tag membership (JSONB array element)
            )
        )
    )
    if category:
        stmt = stmt.where(Spot.category == category)
    stmt = stmt.order_by(relevance.desc(), Spot.updated_at.desc()).limit(limit)
    return [_row_to_out(r) for r in db.execute(stmt).all()]
