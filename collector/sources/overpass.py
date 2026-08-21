"""OpenStreetMap Overpass API source (real data, tier 2).

License: OpenStreetMap data is © OpenStreetMap contributors, ODbL 1.0. Store
attribution and the element URL as the source; verify redistribution terms.

Queries tourism / historic / natural POIs per Kansai prefecture (admin_level=4
boundary by name) so each result gets a correct prefecture code. Network and
parse failures are captured in `self.errors` (never raised) so the daily job
still succeeds on the offline fixture sources.

This sandbox blocks the Overpass host at the egress proxy, so live fetching is
validated in the docker deployment; `parse_elements` is unit-tested offline.
"""

from __future__ import annotations

import os
from urllib.parse import quote

from records import RawRecord
from sources.base import SourceAdapter


def _image_from_tags(tags: dict) -> str | None:
    """Extract an image URL from common OSM tags (image / wikimedia_commons)."""
    img = tags.get("image")
    if img and img.startswith("http"):
        return img
    commons = tags.get("wikimedia_commons")
    if commons and commons.startswith("File:"):
        fname = commons[len("File:"):]
        return "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(fname)
    return None

# Kansai prefectures: name (for Overpass area) -> JIS code (our prefectures.code)
KANSAI = {
    "大阪府": "27", "京都府": "26", "兵庫県": "28",
    "奈良県": "29", "滋賀県": "25", "和歌山県": "30",
}

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"


def _category(tags: dict) -> tuple[str, str | None]:
    t = tags
    if t.get("historic") in {"castle", "castle_wall", "fort"}:
        return "sightseeing", "castle"
    if t.get("historic") in {"ruins", "archaeological_site"}:
        return "sightseeing", "ruins"
    if t.get("amenity") == "place_of_worship" or t.get("historic") in {"temple", "shrine"}:
        return "sightseeing", t.get("religion") or "temple"
    if t.get("tourism") in {"museum", "gallery", "artwork"}:
        return "culture", t.get("tourism")
    if t.get("tourism") in {"zoo", "aquarium", "theme_park"}:
        return "sightseeing", t.get("tourism")
    if t.get("tourism") == "viewpoint":
        return "sightseeing", "viewpoint"
    if t.get("natural") in {"peak", "waterfall", "beach", "bay", "cape"}:
        return "nature", t.get("natural")
    if t.get("leisure") == "park":
        return "nature", "park"
    if t.get("tourism") == "attraction":
        return "sightseeing", "attraction"
    return "sightseeing", t.get("tourism") or t.get("historic") or t.get("natural")


def parse_elements(elements: list[dict], prefecture_code: str) -> list[RawRecord]:
    """Convert Overpass JSON elements to RawRecords (pure; unit-tested)."""
    out: list[RawRecord] = []
    for el in elements:
        tags = el.get("tags") or {}
        name = tags.get("name")
        if not name:
            continue
        if el.get("type") == "node":
            lat, lng = el.get("lat"), el.get("lon")
        else:  # way / relation -> center
            center = el.get("center") or {}
            lat, lng = center.get("lat"), center.get("lon")
        if lat is None or lng is None:
            continue
        category, subcategory = _category(tags)
        osm_url = f"https://www.openstreetmap.org/{el.get('type')}/{el.get('id')}"
        out.append(RawRecord(
            source_key="osm_overpass",
            external_id=f"{el.get('type')}/{el.get('id')}",
            name=name,
            url=tags.get("website") or osm_url,
            description=tags.get("description"),
            lat=float(lat), lng=float(lng),
            category=category, subcategory=subcategory,
            prefecture_code=prefecture_code,
            official_url=tags.get("website"),
            image_url=_image_from_tags(tags),
            image_license="See source (OSM tag / Wikimedia Commons)",
            license_note="© OpenStreetMap contributors, ODbL 1.0",
        ))
    return out


def _query(pref_name: str) -> str:
    return f"""
[out:json][timeout:60];
area["name"="{pref_name}"]["admin_level"="4"]->.a;
(
  nwr["tourism"~"attraction|viewpoint|museum|gallery|artwork|zoo|aquarium|theme_park"]["name"](area.a);
  nwr["historic"~"castle|ruins|monument|memorial|archaeological_site"]["name"](area.a);
  nwr["natural"~"peak|waterfall|beach|cape"]["name"](area.a);
  nwr["leisure"="park"]["name"](area.a);
);
out center 120;
""".strip()


class OverpassSource(SourceAdapter):
    key = "osm_overpass"
    name = "OpenStreetMap (Overpass API)"
    source_type = "opendata"
    tier = 2
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
                resp = httpx.post(self.endpoint, data={"data": _query(pref_name)},
                                  timeout=90.0, headers=headers)
                resp.raise_for_status()
                records.extend(parse_elements(resp.json().get("elements", []), code))
            except Exception as exc:  # noqa: BLE001 - classify below
                etype = "timeout" if "Timeout" in type(exc).__name__ else "http"
                self.errors.append((etype, f"overpass {pref_name}: {exc}"))
        return records
