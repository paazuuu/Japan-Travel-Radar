"""YouTube public data (tier 2).

Uses the official Data API when YOUTUBE_API_KEY is set; otherwise returns an
empty list (no scraping). This keeps the pipeline legal-by-default: public API
only, per 04/12.
"""

from __future__ import annotations

import os

from records import RawRecord
from sources.base import SourceAdapter


class YouTubeSource(SourceAdapter):
    key = "youtube"
    name = "YouTube Public Data API"
    source_type = "youtube"
    tier = 2
    source_url = "https://developers.google.com/youtube/v3"
    license_note = "Metadata via official Data API; no downloading of content."

    def __init__(self) -> None:
        self.api_key = os.environ.get("YOUTUBE_API_KEY", "")
        self.query = os.environ.get("YOUTUBE_QUERY", "関西 旅行 観光")
        self.errors: list[tuple[str, str]] = []

    def fetch(self) -> list[RawRecord]:
        if not self.api_key:
            # No credentials -> nothing collected (never scrape).
            return []
        try:
            import httpx
        except Exception as exc:  # pragma: no cover
            self.errors.append(("parse", f"httpx unavailable: {exc}"))
            return []
        try:
            resp = httpx.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": self.query,
                    "type": "video",
                    "maxResults": 25,
                    "key": self.api_key,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
        except Exception as exc:
            self.errors.append(("http", f"youtube: {exc}"))
            return []

        out: list[RawRecord] = []
        for item in resp.json().get("items", []):
            vid = item.get("id", {}).get("videoId")
            sn = item.get("snippet", {})
            title = sn.get("title")
            if not (vid and title):
                continue
            out.append(
                RawRecord(
                    source_key=self.key,
                    external_id=vid,
                    name=title,
                    url=f"https://www.youtube.com/watch?v={vid}",
                    description=sn.get("description"),
                    license_note=self.license_note,
                )
            )
        return out
