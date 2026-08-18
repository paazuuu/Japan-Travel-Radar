"""MVP1: verify the API routes are registered (no DB required).

Uses the OpenAPI schema so it runs without a live PostgreSQL/PostGIS.
"""

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/none")

from app.main import app  # noqa: E402

client = TestClient(app)


def test_openapi_lists_mvp1_routes():
    paths = client.get("/openapi.json").json()["paths"]
    expected = {
        "/api/v1/spots",
        "/api/v1/spots/{spot_id}",
        "/api/v1/spots/nearby",
        "/api/v1/restaurants",
        "/api/v1/restaurants/nearby",
        "/api/v1/search",
        "/api/v1/spots/{spot_id}/analysis",
        "/api/v1/admin/sources",
        "/api/v1/admin/collector-runs",
        "/api/v1/admin/errors",
        "/api/v1/rankings/{kind}",
        "/api/v1/admin/spots/{spot_id}/score",
        "/api/v1/planner/generate",
        "/api/v1/planner/{plan_id}",
    }
    missing = expected - set(paths)
    assert not missing, f"missing routes: {missing}"


def test_nearby_validation_rejects_bad_lat():
    # 999 is out of range; FastAPI should 422 before touching the DB.
    resp = client.get("/api/v1/spots/nearby", params={"lat": 999, "lng": 135})
    assert resp.status_code == 422
