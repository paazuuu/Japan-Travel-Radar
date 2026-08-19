"""Simple API-key auth for admin endpoints (MVP).

Reads ADMIN_API_KEY from the environment at request time (not via cached
settings) so it is easy to configure per-deploy and to test. Full user accounts
/ JWT arrive with public launch (Stage 9); this closes the immediate hole of an
unauthenticated admin surface.
"""

from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException


def require_admin(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    key = os.environ.get("ADMIN_API_KEY", "")
    if not key:
        # Fail closed: an unconfigured key must not leave admin open.
        raise HTTPException(status_code=503, detail="admin auth not configured: set ADMIN_API_KEY")
    if not x_admin_key or not hmac.compare_digest(x_admin_key, key):
        raise HTTPException(status_code=401, detail="invalid or missing X-Admin-Key")
