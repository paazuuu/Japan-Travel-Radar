"""Configured open-data datasets with column mapping (real municipal data).

Real Japanese tourism open data comes as CSV (often Shift_JIS) or JSON with
arbitrary Japanese column names. This source reads a config file describing each
dataset — its URL/format/encoding and a column mapping — and normalizes every
row into a RawRecord. No code change is needed to add a new dataset.

Config file (default collector/config/opendata_datasets.json, override with
OPENDATA_CONFIG) is a JSON array of dataset descriptors:

    {
      "key": "osaka_kanko",
      "name": "大阪府 観光施設オープンデータ",
      "enabled": true,
      "url": "https://.../spots.csv",       // or "path" for a local file
      "format": "csv",                        // csv | json
      "encoding": "utf-8-sig",                // csv only; utf-8-sig / cp932 ...
      "json_path": "data",                    // json only: key holding the array
      "license_note": "CC BY 4.0",
      "source_type": "opendata",
      "tier": 1,
      "mapping_preset": "suishou_kanko",      // optional column-name preset
      "mapping": { "name": ["名称"], "lat": ["緯度"], ... },  // overrides/extends
      "defaults": { "prefecture_code": "27", "category": "sightseeing" }
    }

`map_rows` is pure and unit-tested; network/parse errors are captured, not raised.
"""

from __future__ import annotations

import csv
import io
import json
import os
from dataclasses import dataclass, field

from records import RawRecord
from sources.base import SourceAdapter

# Prefecture name (any of full/short) -> JIS code. Full 47 for robustness.
PREF_NAME_TO_CODE = {
    "北海道": "01", "青森県": "02", "岩手県": "03", "宮城県": "04", "秋田県": "05",
    "山形県": "06", "福島県": "07", "茨城県": "08", "栃木県": "09", "群馬県": "10",
    "埼玉県": "11", "千葉県": "12", "東京都": "13", "神奈川県": "14", "新潟県": "15",
    "富山県": "16", "石川県": "17", "福井県": "18", "山梨県": "19", "長野県": "20",
    "岐阜県": "21", "静岡県": "22", "愛知県": "23", "三重県": "24", "滋賀県": "25",
    "京都府": "26", "大阪府": "27", "兵庫県": "28", "奈良県": "29", "和歌山県": "30",
    "鳥取県": "31", "島根県": "32", "岡山県": "33", "広島県": "34", "山口県": "35",
    "徳島県": "36", "香川県": "37", "愛媛県": "38", "高知県": "39", "福岡県": "40",
    "佐賀県": "41", "長崎県": "42", "熊本県": "43", "大分県": "44", "宮崎県": "45",
    "鹿児島県": "46", "沖縄県": "47",
}

# Column-name presets. Values are candidate column names (first match wins).
MAPPING_PRESETS: dict[str, dict[str, list[str]]] = {
    # デジタル庁「推奨データセット（観光施設一覧）」標準の列名
    "suishou_kanko": {
        "name": ["名称", "名称_通称", "施設名", "スポット名"],
        "name_en": ["名称_英語"],
        "lat": ["緯度", "latitude", "lat"],
        "lng": ["経度", "longitude", "lng", "lon"],
        "description": ["説明", "概要", "紹介文"],
        "official_url": ["URL", "ホームページ", "リンク"],
        "access": ["アクセス方法", "交通アクセス"],
        "address": ["住所", "所在地", "方書"],
        "prefecture_name": ["都道府県名"],
        "external_id": ["POIコード", "ID", "id"],
        "category": ["カテゴリ", "分類", "種別"],
    },
}


@dataclass
class DatasetSpec:
    key: str
    name: str
    mapping: dict[str, list[str]]
    defaults: dict[str, str] = field(default_factory=dict)
    license_note: str | None = None
    source_type: str = "opendata"
    tier: int = 1
    fmt: str = "csv"
    encoding: str = "utf-8-sig"
    json_path: str | None = None
    url: str | None = None
    path: str | None = None
    enabled: bool = True


def build_spec(desc: dict) -> DatasetSpec:
    mapping = dict(MAPPING_PRESETS.get(desc.get("mapping_preset", ""), {}))
    for k, v in (desc.get("mapping") or {}).items():
        mapping[k] = v  # explicit mapping overrides preset
    return DatasetSpec(
        key=desc["key"], name=desc["name"], mapping=mapping,
        defaults=desc.get("defaults", {}), license_note=desc.get("license_note"),
        source_type=desc.get("source_type", "opendata"), tier=int(desc.get("tier", 1)),
        fmt=desc.get("format", "csv"), encoding=desc.get("encoding", "utf-8-sig"),
        json_path=desc.get("json_path"), url=desc.get("url"), path=desc.get("path"),
        enabled=bool(desc.get("enabled", True)),
    )


def _pick(row: dict, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in row and str(row[col]).strip() not in ("", "None"):
            return str(row[col]).strip()
    return None


def _to_float(v: str | None) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace("°", "").strip())
    except ValueError:
        return None


def map_rows(rows: list[dict], spec: DatasetSpec) -> list[RawRecord]:
    """Map raw dataset rows -> RawRecords using the spec (pure; unit-tested)."""
    out: list[RawRecord] = []
    m = spec.mapping
    d = spec.defaults
    for row in rows:
        name = _pick(row, m.get("name", [])) or d.get("name")
        if not name:
            continue

        pref_code = None
        pref_name = _pick(row, m.get("prefecture_name", []))
        if pref_name:
            pref_code = PREF_NAME_TO_CODE.get(pref_name)
        if not pref_code:
            pref_code = _pick(row, m.get("prefecture_code", [])) or d.get("prefecture_code")

        description = _pick(row, m.get("description", []))
        address = _pick(row, m.get("address", []))
        if not description and address:
            description = address  # keep the address as a fallback description

        out.append(RawRecord(
            source_key=spec.key,
            external_id=_pick(row, m.get("external_id", [])) or name,
            name=name,
            url=_pick(row, m.get("official_url", [])),
            description=description,
            lat=_to_float(_pick(row, m.get("lat", []))),
            lng=_to_float(_pick(row, m.get("lng", []))),
            category=_pick(row, m.get("category", [])) or d.get("category"),
            subcategory=_pick(row, m.get("subcategory", [])) or d.get("subcategory"),
            prefecture_code=pref_code,
            official_url=_pick(row, m.get("official_url", [])),
            license_note=spec.license_note,
        ))
    return out


def parse_csv(data: bytes, encoding: str) -> list[dict]:
    for enc in [encoding, "utf-8-sig", "cp932", "utf-8"]:
        try:
            text = data.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:  # pragma: no cover
        text = data.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


def _extract_json_array(payload, json_path: str | None) -> list[dict]:
    if json_path:
        for key in json_path.split("."):
            payload = payload.get(key, []) if isinstance(payload, dict) else []
    if isinstance(payload, dict):
        payload = payload.get("data") or payload.get("items") or payload.get("results") or []
    return payload if isinstance(payload, list) else []


def _config_path() -> str:
    default = os.path.join(os.path.dirname(__file__), "..", "config", "opendata_datasets.json")
    return os.environ.get("OPENDATA_CONFIG", default)


def load_specs() -> list[DatasetSpec]:
    path = _config_path()
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [build_spec(d) for d in json.load(fh)]


class ConfiguredDatasetsSource(SourceAdapter):
    key = "opendata_datasets"
    name = "Configured municipal open-data datasets"
    source_type = "opendata"
    tier = 1
    license_note = "Per-dataset license; see docs/DATA_SOURCES.md"

    def __init__(self) -> None:
        self.disabled = os.environ.get("COLLECTOR_DISABLE_NETWORK") == "1"
        self.errors: list[tuple[str, str]] = []
        try:
            self.specs = load_specs()
        except Exception as exc:  # bad config shouldn't crash the run
            self.specs = []
            self.errors.append(("parse", f"opendata config: {exc}"))

    def _read_local(self, spec: DatasetSpec) -> list[dict]:
        base = os.path.dirname(__file__)
        full = spec.path if os.path.isabs(spec.path) else os.path.join(base, spec.path)
        with open(full, "rb") as fh:
            raw = fh.read()
        return parse_csv(raw, spec.encoding) if spec.fmt == "csv" else _extract_json_array(json.loads(raw), spec.json_path)

    def fetch(self) -> list[RawRecord]:
        records: list[RawRecord] = []
        for spec in self.specs:
            if not spec.enabled:
                continue
            try:
                if spec.path:  # local file (offline sample) — always available
                    rows = self._read_local(spec)
                elif spec.url:
                    if self.disabled:
                        continue
                    import httpx
                    resp = httpx.get(spec.url, timeout=30.0, follow_redirects=True,
                                     headers={"User-Agent": "JapanTravelRadar/0.1 (collector)"})
                    resp.raise_for_status()
                    rows = (parse_csv(resp.content, spec.encoding) if spec.fmt == "csv"
                            else _extract_json_array(resp.json(), spec.json_path))
                else:
                    continue
                records.extend(map_rows(rows, spec))
            except Exception as exc:  # noqa: BLE001
                etype = "timeout" if "Timeout" in type(exc).__name__ else "http"
                self.errors.append((etype, f"dataset {spec.key}: {exc}"))
        return records
