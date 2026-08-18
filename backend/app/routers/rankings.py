"""Ranking endpoints (13, 06). Ranks published spots by the latest trend scores.

Kinds:
  trending  -> overall trend_score
  rising    -> growth_score (急上昇)
  new       -> novelty_score (新着)
  seasonal  -> seasonality_score (季節おすすめ)
  popular   -> engagement_score (総合人気の代理)
  food      -> spots whose AI food_tags are non-empty, by trend_score
Each item includes the component breakdown and an `is_reference` flag (06).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from geoalchemy2 import Geometry
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Spot, SpotAnalysis, TrendScore
from app.schemas import RankingItem

router = APIRouter(prefix="/rankings", tags=["rankings"])

_LAT = func.ST_Y(cast(Spot.location, Geometry))
_LNG = func.ST_X(cast(Spot.location, Geometry))
_TS = TrendScore
_A = SpotAnalysis

_ORDER = {
    "trending": _TS.trend_score,
    "rising": _TS.growth_score,
    "new": _TS.novelty_score,
    "seasonal": _TS.seasonality_score,
    "popular": _TS.engagement_score,
}


def _latest_date_subq():
    return select(func.max(_TS.score_date)).scalar_subquery()


def _query(order_col, db: Session, category: str | None, prefecture_id, limit: int,
           food_only: bool = False):
    stmt = (
        select(Spot, _LAT, _LNG, _A.summary, _A.confidence, _TS)
        .join(_TS, _TS.spot_id == Spot.id)
        .outerjoin(_A, _A.spot_id == Spot.id)
        .where(Spot.status == "published")
        .where(_TS.score_date == _latest_date_subq())
    )
    if category:
        stmt = stmt.where(Spot.category == category)
    if prefecture_id:
        stmt = stmt.where(Spot.prefecture_id == prefecture_id)
    if food_only:
        stmt = stmt.where(func.jsonb_array_length(_A.food_tags) > 0)
    stmt = stmt.order_by(order_col.desc()).limit(limit)
    return db.execute(stmt).all()


def _to_item(row) -> RankingItem:
    spot: Spot = row[0]
    ts: TrendScore = row[5]
    return RankingItem(
        id=spot.id,
        name=spot.name,
        category=spot.category,
        prefecture_id=spot.prefecture_id,
        lat=row[1],
        lng=row[2],
        ai_summary=row[3],
        ai_confidence=float(row[4]) if row[4] is not None else None,
        trend_score=float(ts.trend_score),
        growth_score=float(ts.growth_score),
        engagement_score=float(ts.engagement_score),
        recency_score=float(ts.recency_score),
        seasonality_score=float(ts.seasonality_score),
        source_diversity_score=float(ts.source_diversity_score),
        novelty_score=float(ts.novelty_score),
        data_confidence_score=float(ts.data_confidence_score),
        is_reference=ts.is_reference,
        score_date=str(ts.score_date),
    )


@router.get("/{kind}", response_model=list[RankingItem])
def ranking(
    kind: str,
    db: Session = Depends(get_db),
    category: str | None = Query(default=None),
    prefecture_id=Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[RankingItem]:
    if kind == "food":
        rows = _query(_TS.trend_score, db, category, prefecture_id, limit, food_only=True)
    else:
        order_col = _ORDER.get(kind, _TS.trend_score)
        rows = _query(order_col, db, category, prefecture_id, limit)
    return [_to_item(r) for r in rows]
