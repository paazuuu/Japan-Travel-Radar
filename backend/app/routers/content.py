"""Content endpoints (13, 09). Generates Chinese/SNS DRAFTS from DB facts.

Draft-only: nothing here publishes to any platform (09: まず下書き生成). Auto-
publish would require each platform's API/ToS review and is intentionally absent.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.content import generator as gen
from app.db import get_db

router = APIRouter(prefix="/content", tags=["content"])


def _facts(db: Session, spot_id: uuid.UUID) -> gen.SpotFacts:
    row = db.execute(text("""
        SELECT s.name, s.name_zh, s.category, s.access_text,
               s.estimated_budget_min, s.estimated_budget_max,
               s.recommended_stay_minutes,
               COALESCE(s.official_url, s.source_url) AS source_url,
               a.summary, a.tags, a.best_season
        FROM spots s
        LEFT JOIN spot_analyses a ON a.spot_id = s.id
        WHERE s.id = :id
    """), {"id": str(spot_id)}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="spot not found")
    r = dict(row)
    return gen.SpotFacts(
        name=r["name"], name_zh=r.get("name_zh"), category=r.get("category"),
        tags=list(r.get("tags") or []), best_season=list(r.get("best_season") or []),
        budget_min=r.get("estimated_budget_min"), budget_max=r.get("estimated_budget_max"),
        access=r.get("access_text"), stay_min=r.get("recommended_stay_minutes"),
        summary=r.get("summary"), source_url=r.get("source_url"),
    )


def _save_draft(db: Session, spot_id: uuid.UUID, platform: str, body: dict) -> dict:
    title = body.get("标题") or body.get("title")
    src = body.get("_source_url")
    db.execute(text("""
        INSERT INTO content_drafts (spot_id, platform, language, title, body, model, source_url)
        VALUES (:spot, :platform, 'zh-CN', :title, CAST(:body AS JSONB), :model, :src)
        ON CONFLICT (spot_id, platform) DO UPDATE SET
            title = EXCLUDED.title, body = EXCLUDED.body, model = EXCLUDED.model,
            source_url = EXCLUDED.source_url, status = 'draft', reviewed = false,
            generated_at = now()
    """), {
        "spot": str(spot_id), "platform": platform, "title": title,
        "body": json.dumps(body, ensure_ascii=False), "model": gen.MODEL_ID, "src": src,
    })
    db.commit()
    return {"spot_id": str(spot_id), "platform": platform, "status": "draft",
            "reviewed": False, "body": body}


def _generate(db: Session, spot_id: uuid.UUID, platform: str) -> dict:
    facts = _facts(db, spot_id)
    body = gen.generate(platform, facts)
    return _save_draft(db, spot_id, platform, body)


@router.post("/xiaohongshu")
def gen_xiaohongshu(spot_id: uuid.UUID = Body(..., embed=True), db: Session = Depends(get_db)) -> dict:
    return _generate(db, spot_id, "xiaohongshu")


@router.post("/wechat")
def gen_wechat(spot_id: uuid.UUID = Body(..., embed=True), db: Session = Depends(get_db)) -> dict:
    return _generate(db, spot_id, "wechat")


@router.post("/video-script")
def gen_video(spot_id: uuid.UUID = Body(..., embed=True), db: Session = Depends(get_db)) -> dict:
    return _generate(db, spot_id, "video_script")


@router.post("/chinese")
def gen_all(spot_id: uuid.UUID = Body(..., embed=True), db: Session = Depends(get_db)) -> dict:
    """Generate all three drafts for a spot (09 完了条件)."""
    return {
        "spot_id": str(spot_id),
        "drafts": {
            "xiaohongshu": _generate(db, spot_id, "xiaohongshu")["body"],
            "wechat": _generate(db, spot_id, "wechat")["body"],
            "video_script": _generate(db, spot_id, "video_script")["body"],
        },
        "note": "全て下書き。公開前に人間レビューが必要です。",
    }


@router.get("/drafts/{spot_id}")
def list_drafts(spot_id: uuid.UUID, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(text("""
        SELECT platform, language, title, body, status, reviewed, generated_at
        FROM content_drafts WHERE spot_id = :id ORDER BY platform
    """), {"id": str(spot_id)}).mappings().all()
    return [dict(r) for r in rows]


@router.post("/drafts/{spot_id}/{platform}/review")
def review_draft(spot_id: uuid.UUID, platform: str,
                 approve: bool = Body(default=True, embed=True), db: Session = Depends(get_db)) -> dict:
    res = db.execute(text("""
        UPDATE content_drafts SET reviewed = true, status = :status
        WHERE spot_id = :id AND platform = :platform RETURNING id
    """), {"id": str(spot_id), "platform": platform, "status": "approved" if approve else "rejected"})
    if res.first() is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="draft not found")
    db.commit()
    return {"reviewed": True, "status": "approved" if approve else "rejected"}
