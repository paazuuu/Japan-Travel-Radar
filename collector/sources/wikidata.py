"""Wikidata SPARQL source (real data, tier 1).

License: Wikidata is CC0 (public domain). Still record provenance (item URL).

Fetches items that are tourist attractions (or subclasses) located in a Kansai
prefecture, with coordinates and a Japanese label. The prefecture is resolved by
its Japanese label so we don't hardcode QIDs. Failures are captured, not raised.

Live host is blocked by this sandbox's egress proxy; `parse_bindings` is
unit-tested offline and the query runs in the docker deployment.
"""

from __future__ import annotations

import os

from records import RawRecord
from sources.base import SourceAdapter

PREF_LABEL_TO_CODE = {
    "大阪府": "27", "京都府": "26", "兵庫県": "28",
    "奈良県": "29", "滋賀県": "25", "和歌山県": "30",
}

DEFAULT_ENDPOINT = "https://query.wikidata.org/sparql"

# Tourist attraction (Q570116) via P31/P279*, located (P131*) in a Kansai pref,
# with coordinates (P625) and a Japanese label.
SPARQL = """
SELECT ?item ?itemLabel ?lat ?lon ?prefLabel WHERE {
  ?item wdt:P31/wdt:P279* wd:Q570116 .
  ?item p:P625/psv:P625 ?coordNode .
  ?coordNode wikibase:geoLatitude ?lat ; wikibase:geoLongitude ?lon .
  ?item wdt:P131* ?pref .
  ?pref wdt:P31 wd:Q50337 .
  ?pref rdfs:label ?prefLabel FILTER (lang(?prefLabel) = "ja")
  FILTER (?prefLabel IN ("大阪府","京都府","兵庫県","奈良県","滋賀県","和歌山県"))
  ?item rdfs:label ?itemLabel FILTER (lang(?itemLabel) = "ja")
}
LIMIT 400
""".strip()


def parse_bindings(bindings: list[dict]) -> list[RawRecord]:
    """Convert SPARQL JSON bindings to RawRecords (pure; unit-tested)."""
    out: list[RawRecord] = []
    for b in bindings:
        def val(k: str):
            return (b.get(k) or {}).get("value")

        item = val("item")
        name = val("itemLabel")
        lat, lon = val("lat"), val("lon")
        pref = val("prefLabel")
        if not (item and name and lat and lon and pref):
            continue
        code = PREF_LABEL_TO_CODE.get(pref)
        if code is None:
            continue
        qid = item.rsplit("/", 1)[-1]
        out.append(RawRecord(
            source_key="wikidata",
            external_id=qid,
            name=name,
            url=item,
            lat=float(lat), lng=float(lon),
            category="sightseeing",
            prefecture_code=code,
            official_url=item,
            license_note="Wikidata, CC0 1.0",
        ))
    return out


class WikidataSource(SourceAdapter):
    key = "wikidata"
    name = "Wikidata (SPARQL)"
    source_type = "opendata"
    tier = 1
    source_url = "https://www.wikidata.org/"
    license_note = "Wikidata, CC0 1.0"

    def __init__(self) -> None:
        self.endpoint = os.environ.get("WIKIDATA_URL", DEFAULT_ENDPOINT)
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
        headers = {
            "User-Agent": "JapanTravelRadar/0.1 (collector; +https://github.com/paazuuu/japan-travel-radar)",
            "Accept": "application/sparql-results+json",
        }
        try:
            resp = httpx.get(self.endpoint, params={"query": SPARQL, "format": "json"},
                             timeout=90.0, headers=headers)
            resp.raise_for_status()
            bindings = resp.json().get("results", {}).get("bindings", [])
            return parse_bindings(bindings)
        except Exception as exc:  # noqa: BLE001
            etype = "timeout" if "Timeout" in type(exc).__name__ else "http"
            self.errors.append((etype, f"wikidata: {exc}"))
            return []
