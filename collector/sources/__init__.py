"""Source adapter registry.

Five distinct legal source types (04: 5種類以上の合法的な情報源):
  tier1: tourism association open data, government open data, official events
  tier2: RSS feeds, YouTube public data
Offline adapters read curated fixtures under sources/data/ so the daily job is
deterministic; network adapters (rss, youtube) degrade gracefully on failure.
"""

from __future__ import annotations

from sources.base import SourceAdapter
from sources.events import EventsOpenDataSource
from sources.government import GovernmentOpenDataSource
from sources.rss import RssSource
from sources.tourism import TourismOpenDataSource
from sources.youtube import YouTubeSource


def build_sources() -> list[SourceAdapter]:
    return [
        TourismOpenDataSource(),
        GovernmentOpenDataSource(),
        EventsOpenDataSource(),
        RssSource(),
        YouTubeSource(),
    ]
