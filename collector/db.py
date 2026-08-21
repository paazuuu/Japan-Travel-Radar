"""Database access for the collector (psycopg 3).

Kept separate from the pipeline logic so normalizer/deduplicator/validator stay
pure and unit-testable without a database.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import psycopg

from deduplicator import KnownKeys
from normalizer import normalize_name
from records import NormalizedSpot


def _dsn() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql://travel:CHANGE_ME@postgres:5432/japan_travel")
    # psycopg accepts postgresql:// ; strip any SQLAlchemy driver suffix.
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def connect() -> psycopg.Connection:
    return psycopg.connect(_dsn())


def upsert_source(conn: psycopg.Connection, *, source_type: str, source_name: str,
                  source_url: str | None, license_note: str | None,
                  collection_method: str) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM sources WHERE source_name = %s LIMIT 1", (source_name,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE sources SET last_collected_at = now() WHERE id = %s", (row[0],))
            return row[0]
        cur.execute(
            """
            INSERT INTO sources (source_type, source_name, source_url, license_note,
                                 collection_method, last_collected_at)
            VALUES (%s, %s, %s, %s, %s, now()) RETURNING id
            """,
            (source_type, source_name, source_url, license_note, collection_method),
        )
        return cur.fetchone()[0]


def prefecture_map(conn: psycopg.Connection) -> dict[str, str]:
    with conn.cursor() as cur:
        cur.execute("SELECT code, id FROM prefectures")
        return {code: pid for code, pid in cur.fetchall()}


def load_known_keys(conn: psycopg.Connection) -> KnownKeys:
    hashes: set[str] = set()
    urls: set[str] = set()
    name_points: list[tuple[str, float, float]] = []
    ext_ids: set[str] = set()
    with conn.cursor() as cur:
        cur.execute("SELECT content_hash FROM raw_items")
        hashes.update(h for (h,) in cur.fetchall() if h)
        cur.execute(
            """
            SELECT name, official_url,
                   ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
                   content_hash, source_key, external_id
            FROM spots
            """
        )
        for name, official_url, lat, lng, chash, skey, ext in cur.fetchall():
            if chash:
                hashes.add(chash)
            if official_url:
                urls.add(official_url)
            if lat is not None and lng is not None:
                name_points.append((normalize_name(name), float(lat), float(lng)))
            if skey and ext:
                ext_ids.add(f"{skey}\x01{ext}")
    return KnownKeys(hashes=hashes, urls=urls, name_points=name_points, ext_ids=ext_ids)


def start_run(conn: psycopg.Connection, source_id: str | None, source_key: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO collector_runs (source_id, source_key) VALUES (%s, %s) RETURNING id",
            (source_id, source_key),
        )
        rid = cur.fetchone()[0]
    conn.commit()
    return rid


def finish_run(conn: psycopg.Connection, run_id: str, *, status: str,
               fetched: int, inserted: int, skipped: int, error_count: int,
               updated: int = 0, pruned: int = 0) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE collector_runs
               SET finished_at = now(), status = %s, fetched = %s,
                   inserted = %s, skipped = %s, error_count = %s,
                   updated = %s, pruned = %s
             WHERE id = %s
            """,
            (status, fetched, inserted, skipped, error_count, updated, pruned, run_id),
        )
    conn.commit()


def log_error(conn: psycopg.Connection, run_id: str | None, source_key: str,
              error_type: str, message: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO collection_errors (run_id, source_key, error_type, message)
            VALUES (%s, %s, %s, %s)
            """,
            (run_id, source_key, error_type, message[:2000]),
        )
    conn.commit()


def _insert_raw_item(cur, spot: NormalizedSpot, source_id: str) -> None:
    cur.execute(
        """
        INSERT INTO raw_items (source_id, source_key, external_id, url, title,
                               content_hash, collected_at, processed)
        VALUES (%s, %s, %s, %s, %s, %s, now(), false)
        ON CONFLICT (content_hash) DO NOTHING
        """,
        (source_id, spot.source_key, spot.external_id, spot.url, spot.name, spot.content_hash),
    )


def insert_spot(conn: psycopg.Connection, spot: NormalizedSpot, *, source_id: str,
                status: str, pref_map: dict[str, str]) -> bool:
    """Insert a NEW spot + its raw_item. Returns True if a row was created."""
    pref_id = pref_map.get(spot.prefecture_code) if spot.prefecture_code else None
    collected = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        _insert_raw_item(cur, spot, source_id)
        geo = ("ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography"
               if spot.lat is not None and spot.lng is not None else "NULL")
        cur.execute(
            f"""
            INSERT INTO spots (name, description, prefecture_id, location, category,
                               subcategory, official_url, image_url, image_license,
                               source_id, source_url, status,
                               content_hash, collected_at, last_collected_at, published_at,
                               license_note, data_class, source_key, external_id)
            VALUES (%(name)s, %(description)s, %(pref_id)s, {geo}, %(category)s,
                    %(subcategory)s, %(official_url)s, %(image_url)s, %(image_license)s,
                    %(source_id)s, %(source_url)s,
                    %(status)s, %(content_hash)s, %(collected)s, %(collected)s, %(published)s,
                    %(license)s, %(data_class)s, %(source_key)s, %(external_id)s)
            ON CONFLICT (content_hash) DO NOTHING
            RETURNING id
            """,
            _spot_params(spot, pref_id, source_id, status, collected),
        )
        created = cur.fetchone() is not None
    conn.commit()
    return created


def update_spot(conn: psycopg.Connection, spot: NormalizedSpot, *, source_id: str,
                pref_map: dict[str, str]) -> str:
    """Refresh an existing spot identified by (source_key, external_id).

    Returns 'updated', or 'locked' when the row was locked by a human override
    (05/12: human edits must survive re-collection). Also records the raw_item.
    """
    pref_id = pref_map.get(spot.prefecture_code) if spot.prefecture_code else None
    collected = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        _insert_raw_item(cur, spot, source_id)
        geo = ("ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography"
               if spot.lat is not None and spot.lng is not None else "location")
        cur.execute(
            f"""
            UPDATE spots SET
                name = %(name)s,
                description = COALESCE(%(description)s, description),
                prefecture_id = COALESCE(%(pref_id)s, prefecture_id),
                location = {geo},
                category = COALESCE(%(category)s, category),
                subcategory = COALESCE(%(subcategory)s, subcategory),
                official_url = COALESCE(%(official_url)s, official_url),
                image_url = COALESCE(%(image_url)s, image_url),
                image_license = COALESCE(%(image_license)s, image_license),
                source_url = %(source_url)s,
                content_hash = %(content_hash)s,
                license_note = %(license)s,
                collected_at = %(collected)s,
                last_collected_at = %(collected)s,
                updated_at = now()
            WHERE source_key = %(source_key)s AND external_id = %(external_id)s
              AND locked = false
            RETURNING id
            """,
            _spot_params(spot, pref_id, source_id, None, collected),
        )
        updated = cur.fetchone() is not None
    conn.commit()
    return "updated" if updated else "locked"


def _spot_params(spot: NormalizedSpot, pref_id, source_id, status, collected) -> dict:
    return {
        "name": spot.name, "description": spot.description, "pref_id": pref_id,
        "lat": spot.lat, "lng": spot.lng, "category": spot.category,
        "subcategory": spot.subcategory, "official_url": spot.official_url,
        "image_url": spot.image_url, "image_license": spot.image_license,
        "source_id": source_id, "source_url": spot.url, "status": status,
        "content_hash": spot.content_hash, "collected": collected,
        "published": spot.published_at, "license": spot.license_note,
        "data_class": spot.data_class, "source_key": spot.source_key,
        "external_id": spot.external_id,
    }


def upsert_event(conn: psycopg.Connection, rec, *, source_id: str, tier: int,
                 pref_map: dict[str, str]) -> str:
    """Insert/refresh an event by (source_key, external_id). Returns inserted/updated/locked."""
    from records import content_hash
    from normalizer import normalize_name

    pref_id = pref_map.get(rec.prefecture_code) if rec.prefecture_code else None
    chash = content_hash(rec.source_key, rec.external_id, normalize_name(rec.name), rec.lat, rec.lng)
    data_class = {1: "A", 2: "B", 3: "C"}.get(tier, "B")
    geo = ("ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography"
           if rec.lat is not None and rec.lng is not None else "NULL")
    params = {
        "name": rec.name, "description": rec.description, "pref_id": pref_id,
        "lat": rec.lat, "lng": rec.lng, "category": rec.category or "event",
        "subcategory": rec.subcategory, "official_url": rec.official_url,
        "image_url": rec.image_url, "image_license": rec.image_license,
        "start_at": rec.start_at, "end_at": rec.end_at, "source_id": source_id,
        "source_url": rec.url, "content_hash": chash, "license": rec.license_note,
        "data_class": data_class, "source_key": rec.source_key, "external_id": rec.external_id,
    }
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO events (name, description, prefecture_id, location, category, subcategory,
                                official_url, image_url, image_license, start_at, end_at,
                                source_id, source_url, content_hash, collected_at, license_note,
                                data_class, source_key, external_id)
            VALUES (%(name)s, %(description)s, %(pref_id)s, {geo}, %(category)s, %(subcategory)s,
                    %(official_url)s, %(image_url)s, %(image_license)s, %(start_at)s, %(end_at)s,
                    %(source_id)s, %(source_url)s, %(content_hash)s, now(), %(license)s,
                    %(data_class)s, %(source_key)s, %(external_id)s)
            ON CONFLICT (source_key, external_id) DO UPDATE SET
                name = EXCLUDED.name, description = COALESCE(EXCLUDED.description, events.description),
                location = EXCLUDED.location, subcategory = EXCLUDED.subcategory,
                official_url = COALESCE(EXCLUDED.official_url, events.official_url),
                image_url = COALESCE(EXCLUDED.image_url, events.image_url),
                start_at = EXCLUDED.start_at, end_at = EXCLUDED.end_at,
                content_hash = EXCLUDED.content_hash, collected_at = now(), updated_at = now()
            WHERE events.locked = false
            RETURNING (xmax = 0) AS inserted
            """,
            params,
        )
        row = cur.fetchone()
    conn.commit()
    if row is None:
        return "locked"
    return "inserted" if row[0] else "updated"


def prune_missing(conn: psycopg.Connection, source_key: str, seen_external_ids: set[str]) -> int:
    """Hide spots from a full-snapshot source that were not seen this run.

    Deletion detection (12): source removed the item -> soft-hide it. Never
    touches locked (human-managed) rows. Returns the number hidden.
    """
    if not seen_external_ids:
        return 0
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE spots SET status = 'hidden', updated_at = now()
            WHERE source_key = %s AND external_id IS NOT NULL
              AND NOT (external_id = ANY(%s))
              AND locked = false AND status <> 'hidden'
            """,
            (source_key, list(seen_external_ids)),
        )
        n = cur.rowcount
    conn.commit()
    return n
