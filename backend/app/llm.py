"""Optional LLM layer for the backend (Anthropic SDK).

Active only when AI_API_KEY (or ANTHROPIC_API_KEY) is set. Every call degrades to
None on missing key / missing SDK / API error, so callers keep their deterministic
behavior. Guardrail: use only the given facts; never invent facts.
"""

from __future__ import annotations

import json
import os


def available() -> bool:
    return bool(os.environ.get("AI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


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


def complete_text(system: str, user: str, max_tokens: int = 512) -> str | None:
    client = _client()
    if client is None:
        return None
    try:
        resp = client.messages.create(
            model=_model(), max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
        return text or None
    except Exception:
        return None


def translate_ja_to_zh(text: str | None) -> str | None:
    """Translate Japanese -> Simplified Chinese, facts only. None on failure."""
    if not text:
        return None
    return complete_text(
        system="あなたはプロの翻訳者です。事実を追加・創作せず、自然な簡体字中国語に翻訳します。訳文のみ返してください。",
        user=f"次の日本語を簡体字中国語に翻訳:\n{text}",
        max_tokens=400,
    )


def plan_summary(context: dict) -> str | None:
    """Natural-language plan summary from structured data only (no invention)."""
    return complete_text(
        system="あなたは旅行プランの要約者です。与えられた構造化データのみを使い、場所や費用を創作しません。日本語で2-3文の魅力的な概要を返してください。",
        user="次のプラン情報を要約:\n" + json.dumps(context, ensure_ascii=False),
        max_tokens=300,
    )
