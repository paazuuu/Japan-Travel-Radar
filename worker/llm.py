"""Optional LLM layer for the analysis worker (Anthropic SDK).

Real LLM is used ONLY when AI_API_KEY (or ANTHROPIC_API_KEY) is set. On any
missing key, missing SDK, API error, or malformed output, callers fall back to
the deterministic rule-based analyzer — so the pipeline always works offline and
is fully unit-testable (tests monkeypatch `complete_json`).

Guardrails (05/12): the model must use only the given facts and must not invent
opening hours, prices, or existence; unknown -> low confidence.
"""

from __future__ import annotations

import json
import os

from analyzer import MODEL_ID, AnalysisResult, analyze

_SYSTEM = (
    "あなたは日本の観光スポットを構造化するアシスタントです。"
    "与えられた事実だけを使い、営業時間・料金・存在などを創作してはいけません。"
    "根拠が乏しい場合は confidence を下げてください。"
    "出力は指定されたJSONオブジェクトのみ（前後の文章やコードフェンス禁止）。"
)


def _model() -> str:
    return os.environ.get("AI_MODEL", "claude-opus-5")


def _client():
    key = os.environ.get("AI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except Exception:
        return None
    try:
        return anthropic.Anthropic(api_key=key)
    except Exception:
        return None


def _strip_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t[: t.rfind("```")]
    return t.strip()


def complete_json(system: str, user: str, max_tokens: int = 1024) -> dict | None:
    """Single LLM call returning a parsed JSON object, or None on any failure."""
    client = _client()
    if client is None:
        return None
    try:
        resp = client.messages.create(
            model=_model(), max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        data = json.loads(_strip_fence(text))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def analyze_llm(name: str, description: str | None, category: str | None) -> AnalysisResult | None:
    """LLM-backed analysis; returns None to signal 'use the rule-based fallback'."""
    prompt = (
        "次のスポットを分析し、JSONで返してください。\n"
        f"名称: {name}\n説明: {description or '（なし）'}\nカテゴリ: {category or '（不明）'}\n\n"
        "JSONスキーマ:\n"
        "{\n"
        '  "summary": "1文の要約(日本語, 事実のみ)",\n'
        '  "categories": ["nature|sightseeing|onsen|culture|event|gourmet のいずれか"],\n'
        '  "tags": ["絶景/写真映え/歴史/文化/自然/温泉/夜景/海/山/家族向け/紅葉/桜 等"],\n'
        '  "best_season": ["spring|summer|autumn|winter の該当"],\n'
        '  "travel_types": ["family|couple|solo|day_trip の該当"],\n'
        '  "food_tags": ["魚/寿司/海鮮/肉/麺/郷土料理/野菜/スイーツ/カフェ 等(該当時のみ)"],\n'
        '  "confidence": 0.0\n'
        "}"
    )
    data = complete_json(_SYSTEM, prompt)
    if not data or "summary" not in data:
        return None

    def _list(key: str) -> list[str]:
        v = data.get(key)
        return [str(x) for x in v] if isinstance(v, list) else []

    try:
        conf = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))

    return AnalysisResult(
        summary=str(data.get("summary") or name)[:140],
        categories=_list("categories") or ([category] if category else []),
        tags=_list("tags"),
        best_season=_list("best_season"),
        travel_types=_list("travel_types"),
        food_tags=_list("food_tags"),
        confidence=conf,
        evidence="LLM分析（事実のみ・創作なしの制約付き）",
        model=_model(),
    )


def analyze_best(name: str, description: str | None, category: str | None) -> AnalysisResult:
    """LLM when configured, else deterministic rule-based (never fails)."""
    return analyze_llm(name, description, category) or analyze(name, description, category)


__all__ = ["complete_json", "analyze_llm", "analyze_best", "MODEL_ID"]
