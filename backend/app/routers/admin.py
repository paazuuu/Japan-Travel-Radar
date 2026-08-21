"""Admin endpoints (13, 12): sources, collector runs, errors, human override.

Read-only monitoring plus the human-override path required by MVP3 (05: 人間に
よる修正が可能). No auth yet — MVP; auth arrives with public launch (Stage 9).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db import get_db

# Every /admin route requires a valid X-Admin-Key header.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _rows(db: Session, sql: str, params: dict | None = None) -> list[dict]:
    result = db.execute(text(sql), params or {})
    return [dict(r) for r in result.mappings().all()]


def _audit(db: Session, action: str, entity: str, entity_id: str, detail: dict) -> None:
    import json
    db.execute(
        text("""
            INSERT INTO audit_log (action, entity, entity_id, detail, actor)
            VALUES (:action, :entity, :eid, CAST(:detail AS JSONB), 'admin')
        """),
        {"action": action, "entity": entity, "eid": entity_id,
         "detail": json.dumps(detail, ensure_ascii=False)},
    )


@router.get("/audit-log")
def audit_log(limit: int = 100, db: Session = Depends(get_db)) -> list[dict]:
    return _rows(db, """
        SELECT action, entity, entity_id, detail, actor, created_at
        FROM audit_log ORDER BY created_at DESC LIMIT :limit
    """, {"limit": limit})


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)) -> list[dict]:
    return _rows(db, """
        SELECT id, source_type, source_name, source_url, last_collected_at
        FROM sources ORDER BY source_name
    """)


@router.get("/collector-runs")
def list_collector_runs(limit: int = 50, db: Session = Depends(get_db)) -> list[dict]:
    return _rows(db, """
        SELECT id, source_key, status, fetched, inserted, updated, skipped, pruned,
               error_count, started_at, finished_at
        FROM collector_runs ORDER BY started_at DESC LIMIT :limit
    """, {"limit": limit})


@router.get("/errors")
def list_errors(limit: int = 100, db: Session = Depends(get_db)) -> list[dict]:
    return _rows(db, """
        SELECT id, run_id, source_key, error_type, message, created_at
        FROM collection_errors ORDER BY created_at DESC LIMIT :limit
    """, {"limit": limit})


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    counts = _rows(db, """
        SELECT
          (SELECT count(*) FROM spots) AS spots,
          (SELECT count(*) FROM spots WHERE status = 'published') AS published_spots,
          (SELECT count(*) FROM restaurants) AS restaurants,
          (SELECT count(*) FROM sources) AS sources,
          (SELECT count(*) FROM spot_analyses) AS analyses,
          (SELECT count(*) FROM trend_scores) AS trend_scores
    """)
    return counts[0] if counts else {}


@router.get("/spots/{spot_id}/score")
def score_breakdown(spot_id: uuid.UUID, db: Session = Depends(get_db)) -> list[dict]:
    """Trend Score component breakdown for a spot (06: 内訳を管理画面で確認)."""
    return _rows(db, """
        SELECT score_date, trend_score, growth_score, engagement_score, recency_score,
               seasonality_score, source_diversity_score, novelty_score,
               data_confidence_score, sample_size, is_reference
        FROM trend_scores WHERE spot_id = :id ORDER BY score_date DESC LIMIT 30
    """, {"id": str(spot_id)})


@router.patch("/spots/{spot_id}")
def override_spot(spot_id: uuid.UUID, payload: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    """Human override of source/AI fields (12: 管理者が公開状態等を修正)."""
    allowed = {"category", "subcategory", "status", "best_season",
               "description", "name", "official_url"}
    fields = {k: v for k, v in payload.items() if k in allowed}
    if not fields:
        raise HTTPException(status_code=400, detail=f"no updatable fields; allowed={sorted(allowed)}")
    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    params = {**fields, "id": str(spot_id)}
    # locked = true so the collector's update job won't overwrite the human edit.
    res = db.execute(text(
        f"UPDATE spots SET {set_clause}, locked = true, updated_at = now() WHERE id = :id RETURNING id"
    ), params)
    if res.first() is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="spot not found")
    _audit(db, "spot.override", "spots", str(spot_id), {"fields": sorted(fields)})
    db.commit()
    return {"updated": sorted(fields), "spot_id": str(spot_id)}


@router.post("/spots/{spot_id}/review")
def review_analysis(spot_id: uuid.UUID, override: dict | None = Body(default=None),
                    db: Session = Depends(get_db)) -> dict:
    """Mark a spot's analysis as human-reviewed so the worker won't overwrite it."""
    import json

    res = db.execute(
        text("""
            UPDATE spot_analyses
               SET reviewed = true, override = COALESCE(CAST(:override AS JSONB), override)
             WHERE spot_id = :id RETURNING id
        """),
        {"id": str(spot_id), "override": json.dumps(override) if override is not None else None},
    )
    if res.first() is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="analysis not found")
    _audit(db, "analysis.review", "spot_analyses", str(spot_id), {"override": override is not None})
    db.commit()
    return {"reviewed": True, "spot_id": str(spot_id)}
