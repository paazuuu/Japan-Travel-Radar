"""Offline checks for the helper behind /spots/{id}/similar."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/none")

from app.routers.spots import _haversine_km  # noqa: E402


def test_haversine_known_distance():
    # Osaka (Umeda) -> Kyoto Station is roughly 40 km as the crow flies
    d = _haversine_km(34.7025, 135.4959, 34.9858, 135.7588)
    assert 35 < d < 45


def test_haversine_zero_and_missing():
    assert _haversine_km(35.0, 135.0, 35.0, 135.0) == 0
    assert _haversine_km(None, 135.0, 35.0, 135.0) is None
