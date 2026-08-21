"""Authentication: register / login / me (Stage 9 foundation)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import security
from app.db import get_db
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Require a valid Bearer token; returns the user row as a dict."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    payload = security.decode_token(authorization.split(" ", 1)[1].strip())
    if not payload:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    row = db.execute(
        text("SELECT id, email, display_name FROM users WHERE id = :id"),
        {"id": payload["sub"]},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=401, detail="user not found")
    return dict(row)


def optional_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict | None:
    """Return the user if a valid token is present, else None (no error)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    payload = security.decode_token(authorization.split(" ", 1)[1].strip())
    if not payload:
        return None
    row = db.execute(
        text("SELECT id, email, display_name FROM users WHERE id = :id"),
        {"id": payload["sub"]},
    ).mappings().first()
    return dict(row) if row else None


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    email = payload.email.strip().lower()
    exists = db.execute(text("SELECT 1 FROM users WHERE email = :e"), {"e": email}).first()
    if exists:
        raise HTTPException(status_code=409, detail="email already registered")
    row = db.execute(
        text("""
            INSERT INTO users (email, password_hash, display_name)
            VALUES (:e, :ph, :dn) RETURNING id, email
        """),
        {"e": email, "ph": security.hash_password(payload.password), "dn": payload.display_name},
    ).mappings().first()
    db.commit()
    return TokenOut(access_token=security.create_token(str(row["id"]), row["email"]))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    email = payload.email.strip().lower()
    row = db.execute(
        text("SELECT id, email, password_hash FROM users WHERE email = :e"), {"e": email}
    ).mappings().first()
    if row is None or not security.verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return TokenOut(access_token=security.create_token(str(row["id"]), row["email"]))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(current_user)) -> UserOut:
    return UserOut(id=user["id"], email=user["email"], display_name=user.get("display_name"))
