from __future__ import annotations

from records import RawRecord
from sources.base import SourceAdapter, load_fixture, rows_to_records


class EventsOpenDataSource(SourceAdapter):
    key = "events_official"
    name = "Official Event Pages (fixture)"
    source_type = "events"
    tier = 1
    source_url = None
    license_note = "Official event listings sample."

    def fetch(self) -> list[RawRecord]:
        rows = load_fixture("events.json")
        return rows_to_records(self.key, rows, license_note=self.license_note)
