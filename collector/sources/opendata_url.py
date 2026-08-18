"""Generic open-data JSON source (real data, tier 1), configured by env.

Lets you plug in specific municipal / tourism-association open-data endpoints
(e.g. 政府標準利用規約 / CC-BY datasets) WITHOUT code changes: set

    OPENDATA_JSON_URLS="https://example.jp/spots.json,https://city.example.jp/data.json"

Each URL must return a JSON array of objects using the same field convention as
the fixtures: name (required), lat, lng, prefecture_code, category, subcategory,
description, official_url, url, license_note. Failures are captured, not raised.
"""

from __future__ import annotations

import os

from records import RawRecord
from sources.base import SourceAdapter, rows_to_records


class OpenDataUrlSource(SourceAdapter):
    key = "opendata_url"
    name = "Configured Open Data (JSON URLs)"
    source_type = "opendata"
    tier = 1
    source_url = None
    license_note = "Per-source license; see each dataset's terms."

    def __init__(self) -> None:
        self.urls = [u.strip() for u in os.environ.get("OPENDATA_JSON_URLS", "").split(",") if u.strip()]
        self.disabled = os.environ.get("COLLECTOR_DISABLE_NETWORK") == "1"
        self.errors: list[tuple[str, str]] = []

    def fetch(self) -> list[RawRecord]:
        if self.disabled or not self.urls:
            return []
        try:
            import httpx
        except Exception as exc:  # pragma: no cover
            self.errors.append(("parse", f"httpx unavailable: {exc}"))
            return []

        records: list[RawRecord] = []
        headers = {"User-Agent": "JapanTravelRadar/0.1 (collector)"}
        for url in self.urls:
            try:
                resp = httpx.get(url, timeout=30.0, headers=headers, follow_redirects=True)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):  # some APIs wrap the array
                    data = data.get("data") or data.get("items") or data.get("results") or []
                if isinstance(data, list):
                    records.extend(rows_to_records(self.key, data, license_note=self.license_note))
            except Exception as exc:  # noqa: BLE001
                etype = "timeout" if "Timeout" in type(exc).__name__ else "http"
                self.errors.append((etype, f"opendata {url}: {exc}"))
        return records
