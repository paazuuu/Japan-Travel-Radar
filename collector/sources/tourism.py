from __future__ import annotations

from records import RawRecord
from sources.base import SourceAdapter, load_fixture, rows_to_records


class TourismOpenDataSource(SourceAdapter):
    key = "tourism_opendata"
    name = "Kansai Tourism Association Open Data (fixture)"
    source_type = "opendata"
    tier = 1
    source_url = "https://www.kansai.gr.jp/"
    license_note = "Open data sample; verify license before public redistribution."

    def fetch(self) -> list[RawRecord]:
        rows = load_fixture("tourism.json")
        return rows_to_records(self.key, rows, license_note=self.license_note)
