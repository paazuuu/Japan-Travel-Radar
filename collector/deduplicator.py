"""Deduplication (04: 重複判定).

Candidate keys: content_hash, official URL, normalized name + coordinate distance.
Pure functions so they can be unit-tested without a DB; the runner supplies the
set of already-known keys pulled from the database.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from records import NormalizedSpot


@dataclass
class KnownKeys:
    hashes: set[str]
    urls: set[str]
    # list of (name_normalized, lat, lng) for spatial-name matching
    name_points: list[tuple[str, float, float]]


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def is_duplicate(spot: NormalizedSpot, known: KnownKeys, radius_m: float = 150.0) -> bool:
    if spot.content_hash in known.hashes:
        return True
    if spot.official_url and spot.official_url in known.urls:
        return True
    if spot.lat is not None and spot.lng is not None:
        for name_norm, lat, lng in known.name_points:
            if name_norm == spot.name_normalized and _haversine_m(spot.lat, spot.lng, lat, lng) <= radius_m:
                return True
    return False


def register(spot: NormalizedSpot, known: KnownKeys) -> None:
    """Mutate `known` so subsequent items in the same batch dedup against this one."""
    known.hashes.add(spot.content_hash)
    if spot.official_url:
        known.urls.add(spot.official_url)
    if spot.lat is not None and spot.lng is not None:
        known.name_points.append((spot.name_normalized, spot.lat, spot.lng))
