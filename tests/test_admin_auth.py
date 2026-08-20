"""Admin API-key auth: /admin/* requires a valid X-Admin-Key (no DB needed)."""

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/none")

from app.main import app  # noqa: E402

# raise_server_exceptions=False so a DB failure surfaces as 500 (not a raise),
# letting us assert that auth passed (status is not 401/503).
client = TestClient(app, raise_server_exceptions=False)


def test_missing_key_is_401(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "s3cret")
    assert client.get("/api/v1/admin/sources").status_code == 401


def test_wrong_key_is_401(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "s3cret")
    r = client.get("/api/v1/admin/sources", headers={"X-Admin-Key": "nope"})
    assert r.status_code == 401


def test_unconfigured_is_503(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    # fail closed: no configured key must not leave admin open
    assert client.get("/api/v1/admin/sources").status_code == 503


def test_correct_key_passes_auth(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "s3cret")
    r = client.get("/api/v1/admin/sources", headers={"X-Admin-Key": "s3cret"})
    # auth passed -> reaches the handler (which then fails on the absent DB).
    assert r.status_code not in (401, 503)
