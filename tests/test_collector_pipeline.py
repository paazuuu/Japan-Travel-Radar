"""MVP2: collector pipeline unit tests (no DB required).

Covers normalize, content-hash stability, dedup by hash/url/name+distance,
validation, and that the 5 source adapters load their fixtures.
"""

import os
import sys

COLLECTOR = os.path.join(os.path.dirname(__file__), "..", "collector")
sys.path.insert(0, COLLECTOR)

from deduplicator import KnownKeys, ext_key, is_duplicate, register  # noqa: E402
from normalizer import normalize, normalize_name  # noqa: E402
from records import RawRecord  # noqa: E402
from sources import build_sources  # noqa: E402
from validator import validate  # noqa: E402


def _raw(**kw) -> RawRecord:
    base = dict(source_key="s", external_id="1", name="テスト", lat=34.7, lng=135.5)
    base.update(kw)
    return RawRecord(**base)


def test_normalize_name_nfkc_and_sample_marker():
    assert normalize_name("ＡＢＣ　カフェ") == "abc カフェ"
    assert normalize_name("海鮮丼（サンプル）") == "海鮮丼"


def test_content_hash_is_stable_and_class_from_tier():
    a = normalize(_raw(), tier=1)
    b = normalize(_raw(), tier=1)
    assert a.content_hash == b.content_hash
    assert a.data_class == "A"          # tier1 -> A
    assert normalize(_raw(), tier=2).data_class == "B"


def test_dedup_by_hash_url_and_name_distance():
    known = KnownKeys(hashes=set(), urls=set(), name_points=[])
    s1 = normalize(_raw(name="大阪城", external_id="x", official_url="http://o"), tier=1)
    assert not is_duplicate(s1, known)
    register(s1, known)
    # same content -> dup by hash
    assert is_duplicate(normalize(_raw(name="大阪城", external_id="x", official_url="http://o"), tier=1), known)
    # different id/hash but same URL -> dup by url
    s_url = normalize(_raw(name="別名", external_id="y", official_url="http://o", lat=None, lng=None), tier=1)
    assert is_duplicate(s_url, known)
    # same normalized name within 150m -> dup
    near = normalize(_raw(name="大阪城", external_id="z", lat=34.70005, lng=135.50005), tier=1)
    assert is_duplicate(near, known)
    # same name but far away -> not dup
    far = normalize(_raw(name="大阪城", external_id="w", lat=35.9, lng=136.9), tier=1)
    assert not is_duplicate(far, known)


def test_validate_statuses():
    ok, status, _ = validate(normalize(_raw(), tier=1))
    assert ok and status == "published"
    ok, status, _ = validate(normalize(_raw(lat=None, lng=None), tier=1))
    assert ok and status == "draft"
    ok, status, _ = validate(normalize(_raw(name=""), tier=1))
    assert not ok and status == "invalid"
    ok, status, _ = validate(normalize(_raw(lat=999, lng=0), tier=1))
    assert not ok


def test_ext_key_and_prune_flags():
    assert ext_key("osm", "node/1") == "osm\x01node/1"
    assert ext_key("osm", None) is None
    by_key = {s.key: s for s in build_sources()}
    # full-snapshot fixture sources prune; incremental feeds must not
    assert by_key["tourism_opendata"].prunes is True
    assert by_key["government_opendata"].prunes is True
    assert by_key["rss"].prunes is False
    assert by_key["youtube"].prunes is False


def test_five_sources_and_offline_fixtures_load():
    sources = build_sources()
    assert len(sources) >= 5
    keys = {s.key for s in sources}
    assert {"tourism_opendata", "government_opendata", "events_official", "rss", "youtube"} <= keys
    # offline tier-1 sources must yield records from fixtures
    by_key = {s.key: s for s in sources}
    assert len(by_key["tourism_opendata"].fetch()) >= 10
    assert len(by_key["government_opendata"].fetch()) >= 8
    assert len(by_key["events_official"].fetch()) >= 6


def test_events_source_is_event_writer_with_dates():
    by_key = {s.key: s for s in build_sources()}
    ev = by_key["events_official"]
    assert ev.writes_events is True and ev.prunes is False
    recs = ev.fetch()
    withdates = [r for r in recs if r.start_at]
    assert len(withdates) >= 6
    assert all(r.category == "event" for r in recs)
