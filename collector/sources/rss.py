"""RSS source (tier 2). Reads feed URLs from env RSS_FEEDS (comma-separated).

Network access and parsing failures are caught and surfaced via the returned
(records, errors) contract used by the runner, so the daily job still succeeds
on the offline tier-1 sources.
"""

from __future__ import annotations

import os
from xml.etree import ElementTree as ET

from records import RawRecord
from sources.base import SourceAdapter


class RssSource(SourceAdapter):
    key = "rss"
    name = "Travel/News RSS Feeds"
    source_type = "rss"
    tier = 2
    license_note = "Headline + link only; full text not stored."

    def __init__(self) -> None:
        self.feeds = [u.strip() for u in os.environ.get("RSS_FEEDS", "").split(",") if u.strip()]
        self.errors: list[tuple[str, str]] = []

    def fetch(self) -> list[RawRecord]:
        records: list[RawRecord] = []
        if not self.feeds:
            return records
        try:
            import httpx  # local import so offline runs don't require it at import time
        except Exception as exc:  # pragma: no cover
            self.errors.append(("parse", f"httpx unavailable: {exc}"))
            return records

        for url in self.feeds:
            try:
                resp = httpx.get(url, timeout=10.0, follow_redirects=True)
                resp.raise_for_status()
                records.extend(self._parse(url, resp.text))
            except httpx.TimeoutException as exc:
                self.errors.append(("timeout", f"{url}: {exc}"))
            except httpx.HTTPStatusError as exc:
                etype = "rate_limit" if exc.response.status_code == 429 else "http"
                self.errors.append((etype, f"{url}: {exc}"))
            except Exception as exc:
                self.errors.append(("parse", f"{url}: {exc}"))
        return records

    def _parse(self, feed_url: str, text: str) -> list[RawRecord]:
        out: list[RawRecord] = []
        root = ET.fromstring(text)
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if not title:
                continue
            out.append(
                RawRecord(
                    source_key=self.key,
                    external_id=link or title,
                    name=title,
                    url=link or None,
                    description=(item.findtext("description") or "").strip() or None,
                    license_note=self.license_note,
                )
            )
        return out
