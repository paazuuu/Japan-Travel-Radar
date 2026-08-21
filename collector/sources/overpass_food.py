"""OpenStreetMap Overpass restaurants (real data, tier 2, ODbL).

Collects amenity=restaurant/cafe/fast_food POIs with a name, per Kansai
prefecture, mapping the OSM `cuisine` tag to food attributes. Writes to the
restaurants table (writes_restaurants). Degrades gracefully like the spot
Overpass source. `parse_restaurants` is unit-tested offline.
"""

from __future__ import annotations

import os

from records import RawRecord
from sources.base import SourceAdapter
from sources.overpass import KANSAI, _image_from_tags

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"


def parse_restaurants(elements: list[dict], prefecture_code: str) -> list[RawRecord]:
    out: list[RawRecord] = []
    for el in elements:
        tags = el.get("tags") or {}
        name = tags.get("name")
        if not name:
            continue
        if el.get("type") == "node":
            lat, lng = el.get("lat"), el.get("lon")
        else:
            center = el.get("center") or {}
            lat, lng = center.get("lat"), center.get("lon")
        if lat is None or lng is None:
            continue
        cuisine = tags.get("cuisine") or tags.get("amenity") or ""
        out.append(RawRecord(
            source_key="osm_restaurants",
            external_id=f"{el.get('type')}/{el.get('id')}",
            name=name,
            url=tags.get("website"),
            description=None,
            lat=float(lat), lng=float(lng),
            category=cuisine.replace(";", ","),
            prefecture_code=prefecture_code,
            official_url=tags.get("website"),
            image_url=_image_from_tags(tags),
            license_note="© OpenStreetMap contributors, ODbL 1.0",
        ))
    return out


def _query(pref_name: str) -> str:
    return f"""
[out:json][timeout:60];
area["name"="{pref_name}"]["admin_level"="4"]->.a;
(
  nwr["amenity"~"restaurant|cafe|fast_food"]["name"](area.a);
);
out center 120;
""".strip()


class OverpassRestaurantSource(SourceAdapter):
    key = "osm_restaurants"
    name = "OpenStreetMap Restaurants (Overpass API)"
    source_type = "opendata"
    tier = 2
    writes_restaurants = True
    source_url = "https://www.openstreetmap.org/copyright"
    license_note = "© OpenStreetMap contributors, ODbL 1.0"

    def __init__(self) -> None:
        self.endpoint = os.environ.get("OVERPASS_URL", DEFAULT_ENDPOINT)
        self.disabled = os.environ.get("COLLECTOR_DISABLE_NETWORK") == "1"
        self.errors: list[tuple[str, str]] = []

    def fetch(self) -> list[RawRecord]:
        if self.disabled:
            return []
        try:
            import httpx
        except Exception as exc:  # pragma: no cover
            self.errors.append(("parse", f"httpx unavailable: {exc}"))
            return []
        records: list[RawRecord] = []
        headers = {"User-Agent": "JapanTravelRadar/0.1 (collector; +https://github.com/paazuuu/japan-travel-radar)"}
        for pref_name, code in KANSAI.items():
            try:
                resp = httpx.post(self.endpoint, data={"data": _query(pref_name)}, timeout=90.0, headers=headers)
                resp.raise_for_status()
                records.extend(parse_restaurants(resp.json().get("elements", []), code))
            except Exception as exc:  # noqa: BLE001
                etype = "timeout" if "Timeout" in type(exc).__name__ else "http"
                self.errors.append((etype, f"overpass-food {pref_name}: {exc}"))
        return records
