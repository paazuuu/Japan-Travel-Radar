"""Shared record types for the collection pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawRecord:
    """A single item as returned by a source adapter (pre-normalization)."""

    source_key: str
    external_id: str | None
    name: str
    url: str | None = None
    description: str | None = None
    lat: float | None = None
    lng: float | None = None
    category: str | None = None
    subcategory: str | None = None
    prefecture_code: str | None = None
    official_url: str | None = None
    image_url: str | None = None
    image_license: str | None = None
    published_at: datetime | None = None
    license_note: str | None = None
    start_at: str | None = None   # events: 'YYYY-MM-DD' or ISO
    end_at: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class NormalizedSpot:
    """A cleaned record ready for dedup / validation / DB insert."""

    source_key: str
    external_id: str | None
    name: str
    name_normalized: str
    url: str | None
    description: str | None
    lat: float | None
    lng: float | None
    category: str | None
    subcategory: str | None
    prefecture_code: str | None
    official_url: str | None
    image_url: str | None
    image_license: str | None
    published_at: datetime | None
    license_note: str | None
    data_class: str
    content_hash: str


def content_hash(source_key: str, external_id: str | None, name_normalized: str,
                 lat: float | None, lng: float | None) -> str:
    """Stable hash used for dedup. Coordinates rounded to ~10m."""
    lat_r = round(lat, 4) if lat is not None else ""
    lng_r = round(lng, 4) if lng is not None else ""
    basis = f"{source_key}|{external_id or ''}|{name_normalized}|{lat_r}|{lng_r}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()
