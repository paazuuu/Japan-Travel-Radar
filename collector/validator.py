"""Validation (04: Validate step; 03: 必須項目が欠けたレコードは公開対象外)."""

from __future__ import annotations

from records import NormalizedSpot

VALID_PREFECTURE_CODES = {"25", "26", "27", "28", "29", "30", "24"}  # Kansai (+Mie)


def validate(spot: NormalizedSpot) -> tuple[bool, str, str | None]:
    """Return (is_valid, publish_status, error_message).

    publish_status: 'published' if complete, 'draft' if usable but missing
    recommended fields, otherwise invalid.
    """
    if not spot.name or len(spot.name_normalized) < 1:
        return False, "invalid", "missing name"

    if spot.lat is None or spot.lng is None:
        # Usable record but not map-ready -> keep as draft, not published.
        return True, "draft", None

    if not (-90 <= spot.lat <= 90 and -180 <= spot.lng <= 180):
        return False, "invalid", f"coordinate out of range ({spot.lat},{spot.lng})"

    if spot.prefecture_code and spot.prefecture_code not in VALID_PREFECTURE_CODES:
        # Outside target region for MVP; keep as draft rather than reject.
        return True, "draft", None

    return True, "published", None
