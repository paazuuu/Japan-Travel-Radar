from __future__ import annotations

from records import RawRecord
from sources.base import SourceAdapter, load_fixture, rows_to_records


class GovernmentOpenDataSource(SourceAdapter):
    key = "government_opendata"
    name = "Local Government Open Data (fixture)"
    source_type = "opendata"
    tier = 1
    source_url = "https://www.data.go.jp/"
    license_note = "Public sector open data sample."

    def fetch(self) -> list[RawRecord]:
        rows = load_fixture("government.json")
        return rows_to_records(self.key, rows, license_note=self.license_note)
