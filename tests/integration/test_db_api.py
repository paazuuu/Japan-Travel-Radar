"""DB-backed integration test — runs in CI against a real Postgres/PostGIS.

Skipped unless RUN_DB_TESTS=1 (so the unit job stays DB-free). The CI
integration job applies all migrations + seeds and runs the collector/worker
once, then this exercises the real API end-to-end.
"""

import os
import sys

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1", reason="requires a live database (RUN_DB_TESTS=1)"
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_health_ok(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database"] is True and body["postgis"] is True


def test_spots_and_nearby(client):
    spots = client.get("/api/v1/spots?limit=100").json()
    assert len(spots) >= 20
    near = client.get("/api/v1/spots/nearby", params={"lat": 34.6873, "lng": 135.5259, "radius": 5000}).json()
    assert len(near) >= 1
    assert near[0]["distance_m"] is not None


def test_events_seeded(client):
    events = client.get("/api/v1/events").json()
    assert len(events) >= 5


def test_rankings_after_worker(client):
    # worker ran once in CI -> trend scores exist
    trending = client.get("/api/v1/rankings/trending").json()
    assert isinstance(trending, list) and len(trending) >= 1
    assert "trend_score" in trending[0]


def test_planner_generates_grounded_plan(client):
    resp = client.post("/api/v1/planner/generate", json={
        "origin": "大阪", "days": 1, "budget": 5000, "party_size": 2,
        "transport": "train", "purpose": "絶景", "food": "魚", "max_spots": 3,
    })
    assert resp.status_code == 200
    plan = resp.json()
    assert plan["items"] and plan["items"][0]["kind"] == "depart"
    assert plan["total_cost"] is not None


def test_content_chinese_draft(client):
    spot_id = client.get("/api/v1/spots?limit=1").json()[0]["id"]
    resp = client.post("/api/v1/content/chinese", json={"spot_id": spot_id})
    assert resp.status_code == 200
    assert "xiaohongshu" in resp.json()["drafts"]


def test_admin_requires_key(client):
    # ADMIN_API_KEY is set in CI; without header -> 401
    assert client.get("/api/v1/admin/stats").status_code == 401
    key = os.environ["ADMIN_API_KEY"]
    stats = client.get("/api/v1/admin/stats", headers={"X-Admin-Key": key}).json()
    assert stats["spots"] >= 20
