"""Rate limiter middleware unit test (no DB)."""

import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.middleware import RateLimiterMiddleware  # noqa: E402


def _client(limit: int) -> TestClient:
    os.environ.pop("RATE_LIMIT_PER_MIN", None)  # let the constructor arg win
    app = FastAPI()
    app.add_middleware(RateLimiterMiddleware, limit_per_min=limit)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return TestClient(app)


def test_allows_under_limit_then_429():
    client = _client(3)
    for _ in range(3):
        assert client.get("/ping").status_code == 200
    r = client.get("/ping")
    assert r.status_code == 429
    assert r.headers.get("Retry-After") == "60"


def test_disabled_when_zero():
    client = _client(0)
    for _ in range(10):
        assert client.get("/ping").status_code == 200
