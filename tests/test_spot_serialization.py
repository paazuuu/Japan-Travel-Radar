"""Regression: SpotOut must not pull the Spot.tags ORM relationship.

Reproduces the CI-caught bug offline: a Spot whose `tags` relationship holds
SpotTag ORM objects must still serialize (tags come from the AI-analysis column).
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DATABASE_URL", "postgresql://x:x@127.0.0.1:1/none")

from app.models import Spot, SpotTag  # noqa: E402
from app.routers import spots as spots_router  # noqa: E402


def test_row_to_out_ignores_orm_tag_relationship():
    spot = Spot(id=uuid.uuid4(), name="播磨の博物館", status="published")
    # Populate the ORM relationship with SpotTag objects (as a real query would).
    spot.tags = [SpotTag(tag="歴史"), SpotTag(tag="文化")]

    row = (spot, 34.716, 134.92, "播磨の考古資料。", ["文化", "歴史"], ["solo"], 0.87)
    out = spots_router._row_to_out(row)

    # tags come from the analysis column (row[4]), not the SpotTag relationship
    assert out.tags == ["文化", "歴史"]
    assert all(isinstance(t, str) for t in out.tags)
    assert out.ai_summary == "播磨の考古資料。"
    assert out.lat == 34.716 and out.lng == 134.92
    assert out.ai_confidence == 0.87
