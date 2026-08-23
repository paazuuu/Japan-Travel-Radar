"""Authenticated user data: favorites and saved plans (server-side)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.routers.auth import current_user
from app.schemas import SpotOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/favorites", response_model=list[SpotOut])
def list_favorites(user: dict = Depends(current_user), db: Session = Depends(get_db)) -> list[SpotOut]:
    rows = db.execute(text("""
        SELECT s.*, ST_Y(s.location::geometry) AS lat, ST_X(s.location::geometry) AS lng
        FROM user_favorites f JOIN spots s ON s.id = f.spot_id
        WHERE f.user_id = :uid ORDER BY f.created_at DESC
    """), {"uid": user["id"]}).mappings().all()
    return [SpotOut(**{k: r[k] for k in r.keys() if k in SpotOut.model_fields}) for r in rows]


@router.put("/favorites/{spot_id}")
def add_favorite(spot_id: uuid.UUID, user: dict = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    exists = db.execute(text("SELECT 1 FROM spots WHERE id = :id"), {"id": str(spot_id)}).first()
    if not exists:
        raise HTTPException(status_code=404, detail="spot not found")
    db.execute(text("""
        INSERT INTO user_favorites (user_id, spot_id) VALUES (:uid, :sid)
        ON CONFLICT (user_id, spot_id) DO NOTHING
    """), {"uid": user["id"], "sid": str(spot_id)})
    db.commit()
    return {"favorited": True, "spot_id": str(spot_id)}


@router.delete("/favorites/{spot_id}")
def remove_favorite(spot_id: uuid.UUID, user: dict = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    db.execute(text("DELETE FROM user_favorites WHERE user_id = :uid AND spot_id = :sid"),
               {"uid": user["id"], "sid": str(spot_id)})
    db.commit()
    return {"favorited": False, "spot_id": str(spot_id)}


@router.get("/plans")
def list_plans(user: dict = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(text("""
        SELECT id, origin, summary, total_cost, within_budget, generated_at
        FROM travel_plans WHERE user_id = :uid ORDER BY generated_at DESC LIMIT 100
    """), {"uid": user["id"]}).mappings().all()
    return [dict(r) for r in rows]
