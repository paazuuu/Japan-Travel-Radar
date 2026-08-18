"""Source adapter registry.

Legal source types (04: 5種類以上の合法的な情報源):
  Offline fixtures (deterministic, always available):
    - tourism / government / official events open-data samples
  Live real data (degrade gracefully; require network):
    - RSS feeds, YouTube public Data API
    - OpenStreetMap Overpass API (ODbL)
    - Wikidata SPARQL (CC0)
    - Configured open-data JSON URLs (per-dataset license)

Network adapters never raise; failures land in collection_errors so the daily
job still succeeds on the offline sources. Disable all network fetching with
COLLECTOR_DISABLE_NETWORK=1.
"""

from __future__ import annotations

from sources.base import SourceAdapter
from sources.events import EventsOpenDataSource
from sources.government import GovernmentOpenDataSource
from sources.opendata_url import OpenDataUrlSource
from sources.overpass import OverpassSource
from sources.rss import RssSource
from sources.tourism import TourismOpenDataSource
from sources.wikidata import WikidataSource
from sources.youtube import YouTubeSource


def build_sources() -> list[SourceAdapter]:
    return [
        # offline fixtures — keep the daily job deterministic
        TourismOpenDataSource(),
        GovernmentOpenDataSource(),
        EventsOpenDataSource(),
        # live real data — enrich the DB when network is available
        OverpassSource(),
        WikidataSource(),
        OpenDataUrlSource(),
        RssSource(),
        YouTubeSource(),
    ]
