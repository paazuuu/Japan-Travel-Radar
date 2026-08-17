"""Normalize raw records into a consistent shape (04: Normalize step)."""

from __future__ import annotations

import re
import unicodedata

from records import NormalizedSpot, RawRecord, content_hash

# Source tier -> governance data class (12_DATA_GOVERNANCE.md)
# A: official/public, B: trusted third party, C: user/SNS, D: AI-estimated
_TIER_TO_CLASS = {1: "A", 2: "B", 3: "C"}

_WS = re.compile(r"\s+")


def normalize_name(name: str) -> str:
    """NFKC + lowercase + collapse whitespace + strip common decorations."""
    n = unicodedata.normalize("NFKC", name or "").strip()
    n = _WS.sub(" ", n)
    # Drop trailing sample/branch markers that shouldn't affect identity.
    n = re.sub(r"[（(](サンプル|sample)[）)]\s*$", "", n, flags=re.IGNORECASE).strip()
    return n.lower()


def normalize(record: RawRecord, tier: int) -> NormalizedSpot:
    name_norm = normalize_name(record.name)
    return NormalizedSpot(
        source_key=record.source_key,
        external_id=record.external_id,
        name=unicodedata.normalize("NFKC", record.name or "").strip(),
        name_normalized=name_norm,
        url=record.url,
        description=(record.description or "").strip() or None,
        lat=record.lat,
        lng=record.lng,
        category=record.category,
        subcategory=record.subcategory,
        prefecture_code=record.prefecture_code,
        official_url=record.official_url or record.url,
        published_at=record.published_at,
        license_note=record.license_note,
        data_class=_TIER_TO_CLASS.get(tier, "B"),
        content_hash=content_hash(
            record.source_key, record.external_id, name_norm, record.lat, record.lng
        ),
    )
