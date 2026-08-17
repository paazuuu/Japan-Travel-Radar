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
    with conn.cursor() as cur:
        cur.execute("SELECT content_hash FROM raw_items")
        hashes.update(h for (h,) in cur.fetchall() if h)
        cur.execute(
            """
            SELECT name, official_url,
                   ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng,
                   content_hash
            FROM spots
            """
        )
        for name, official_url, lat, lng, chash in cur.fetchall():
            if chash:
                hashes.add(chash)
            if official_url:
                urls.add(official_url)
            if lat is not None and lng is not None:
                name_points.append((normalize_name(name), float(lat), float(lng)))
    return KnownKeys(hashes=hashes, urls=urls, name_points=name_points)


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
               fetched: int, inserted: int, skipped: int, error_count: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE collector_runs
               SET finished_at = now(), status = %s, fetched = %s,
                   inserted = %s, skipped = %s, error_count = %s
             WHERE id = %s
            """,
            (status, fetched, inserted, skipped, error_count, run_id),
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


def insert_spot(conn: psycopg.Connection, spot: NormalizedSpot, *, source_id: str,
                status: str, pref_map: dict[str, str]) -> bool:
    """Insert a spot + its raw_item. Returns True if a new spot row was created."""
    pref_id = pref_map.get(spot.prefecture_code) if spot.prefecture_code else None
    collected = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_items (source_id, source_key, external_id, url, title,
                                   content_hash, collected_at, processed)
            VALUES (%s, %s, %s, %s, %s, %s, now(), false)
            ON CONFLICT (content_hash) DO NOTHING
            """,
            (source_id, spot.source_key, spot.external_id, spot.url, spot.name, spot.content_hash),
        )
        if spot.lat is not None and spot.lng is not None:
            geo = "ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography"
        else:
            geo = "NULL"
        cur.execute(
            f"""
            INSERT INTO spots (name, description, prefecture_id, location, category,
                               subcategory, official_url, source_id, source_url, status,
                               content_hash, collected_at, published_at, license_note,
                               data_class, source_key, external_id)
            VALUES (%(name)s, %(description)s, %(pref_id)s, {geo}, %(category)s,
                    %(subcategory)s, %(official_url)s, %(source_id)s, %(source_url)s,
                    %(status)s, %(content_hash)s, %(collected)s, %(published)s,
                    %(license)s, %(data_class)s, %(source_key)s, %(external_id)s)
            ON CONFLICT (content_hash) DO NOTHING
            RETURNING id
            """,
            {
                "name": spot.name,
                "description": spot.description,
                "pref_id": pref_id,
                "lat": spot.lat,
                "lng": spot.lng,
                "category": spot.category,
                "subcategory": spot.subcategory,
                "official_url": spot.official_url,
                "source_id": source_id,
                "source_url": spot.url,
                "status": status,
                "content_hash": spot.content_hash,
                "collected": collected,
                "published": spot.published_at,
                "license": spot.license_note,
                "data_class": spot.data_class,
                "source_key": spot.source_key,
                "external_id": spot.external_id,
            },
        )
        created = cur.fetchone() is not None
    conn.commit()
    return created
