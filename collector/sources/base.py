"""Source adapter base class + fixture helpers."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime

from records import RawRecord

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class SourceAdapter(ABC):
    #: stable key stored on every record (source_key)
    key: str
    #: human-readable name stored in `sources`
    name: str
    #: legal source type (04): official / opendata / events / rss / youtube ...
    source_type: str
    #: collection tier (1/2/3) -> governance data class
    tier: int
    #: reference URL / license
    source_url: str | None = None
    license_note: str | None = None

    @abstractmethod
    def fetch(self) -> list[RawRecord]:
        """Return raw records. Must not raise for expected empty/degraded cases."""
        raise NotImplementedError


def load_fixture(filename: str) -> list[dict]:
    path = os.path.join(_DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def rows_to_records(source_key: str, rows: list[dict],
                    published_at: datetime | None = None,
                    license_note: str | None = None) -> list[RawRecord]:
    records: list[RawRecord] = []
    for row in rows:
        if not row.get("name"):
            continue  # external data can be messy; a name is required downstream
        records.append(
            RawRecord(
                source_key=source_key,
                external_id=str(row.get("external_id") or row.get("id") or row.get("name")),
                name=row["name"],
                url=row.get("url") or row.get("official_url"),
                description=row.get("description"),
                lat=row.get("lat"),
                lng=row.get("lng"),
                category=row.get("category"),
                subcategory=row.get("subcategory"),
                prefecture_code=str(row["prefecture_code"]) if row.get("prefecture_code") else None,
                official_url=row.get("official_url") or row.get("url"),
                published_at=published_at,
                license_note=license_note or row.get("license_note"),
            )
        )
    return records
