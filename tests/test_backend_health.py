"""Smoke test for the backend health endpoint.

Runs without a database: /health must return 200 and report DB/PostGIS
as unavailable (status "degraded") rather than raising.
"""

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/none")

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert body["status"] in {"ok", "degraded"}
    assert set(body).issuperset({"database", "postgis"})


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "japan-travel-radar-backend"
