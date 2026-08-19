"""LLM layer: fallback to rules when unconfigured; parse when the API answers.

No network / no anthropic SDK needed — the LLM call boundary is monkeypatched.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))

import llm as worker_llm  # noqa: E402
from analyzer import MODEL_ID  # noqa: E402


def test_analyze_best_falls_back_to_rules_without_key(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = worker_llm.analyze_best("大阪城", "天守閣と公園。", "sightseeing")
    assert r.model == MODEL_ID          # rule-based model id
    assert "歴史" in r.tags


def test_analyze_llm_returns_none_when_call_fails(monkeypatch):
    monkeypatch.setattr(worker_llm, "complete_json", lambda *a, **k: None)
    assert worker_llm.analyze_llm("X", None, None) is None


def test_analyze_llm_parses_structured_output(monkeypatch):
    monkeypatch.setenv("AI_MODEL", "claude-opus-5")
    monkeypatch.setattr(worker_llm, "complete_json", lambda *a, **k: {
        "summary": "京都の名刹。",
        "categories": ["sightseeing"],
        "tags": ["歴史", "写真映え"],
        "best_season": ["autumn"],
        "travel_types": ["solo"],
        "food_tags": [],
        "confidence": 1.5,  # out of range -> clamped
    })
    r = worker_llm.analyze_llm("清水寺", "清水の舞台。", "sightseeing")
    assert r is not None
    assert r.model == "claude-opus-5"
    assert r.tags == ["歴史", "写真映え"]
    assert r.confidence == 1.0          # clamped to [0,1]


def test_analyze_best_uses_llm_when_available(monkeypatch):
    monkeypatch.setattr(worker_llm, "analyze_llm", lambda *a, **k: worker_llm.AnalysisResult(
        summary="s", categories=[], tags=["絶景"], best_season=[], travel_types=[],
        food_tags=[], confidence=0.9, evidence="llm", model="claude-opus-5"))
    r = worker_llm.analyze_best("x", None, None)
    assert r.model == "claude-opus-5" and r.tags == ["絶景"]
