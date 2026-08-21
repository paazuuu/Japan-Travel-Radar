"""Collector runner: Fetch -> Normalize -> Deduplicate -> Validate -> DB (04).

Entry point for the daily job. Each source runs independently so one failing
source never aborts the others; every error is logged to collection_errors.
"""

from __future__ import annotations

import sys

import db as dbmod
import deduplicator as dedup
from normalizer import normalize
from sources import build_sources
from sources.base import SourceAdapter
from validator import validate


def run_source(conn, source: SourceAdapter, pref_map, known) -> dict:
    source_id = dbmod.upsert_source(
        conn,
        source_type=source.source_type,
        source_name=source.name,
        source_url=getattr(source, "source_url", None),
        license_note=getattr(source, "license_note", None),
        collection_method=source.source_type,
    )
    run_id = dbmod.start_run(conn, source_id, source.key)

    # Event sources write to the events table (first-class), not spots.
    if getattr(source, "writes_events", False):
        return _run_event_source(conn, source, source_id, run_id, pref_map)

    fetched = inserted = updated = skipped = errors = pruned = 0
    seen_ext: set[str] = set()
    try:
        records = source.fetch()
    except Exception as exc:  # source-level failure
        dbmod.log_error(conn, run_id, source.key, "fetch", str(exc))
        dbmod.finish_run(conn, run_id, status="failed", fetched=0, inserted=0, skipped=0, error_count=1)
        return {"source": source.key, "status": "failed", "inserted": 0, "errors": 1}

    # Adapter-level soft errors (network/parse) collected without aborting.
    for etype, msg in getattr(source, "errors", []):
        dbmod.log_error(conn, run_id, source.key, etype, msg)
        errors += 1

    for record in records:
        fetched += 1
        try:
            spot = normalize(record, source.tier)
            if spot.external_id:
                seen_ext.add(spot.external_id)
            key = dedup.ext_key(spot.source_key, spot.external_id)

            ok, status, verr = validate(spot)
            if not ok:
                dbmod.log_error(conn, run_id, source.key, "validation", verr or "invalid")
                errors += 1
                continue

            if key and key in known.ext_ids:
                # Same source item seen before -> UPDATE (refresh) instead of skip.
                if spot.content_hash in known.hashes:
                    skipped += 1  # unchanged since last collection
                else:
                    res = dbmod.update_spot(conn, spot, source_id=source_id, pref_map=pref_map)
                    updated += 1 if res == "updated" else 0
                    skipped += 1 if res == "locked" else 0
                    known.hashes.add(spot.content_hash)
                continue

            if dedup.is_duplicate(spot, known):
                skipped += 1
                continue
            created = dbmod.insert_spot(conn, spot, source_id=source_id, status=status, pref_map=pref_map)
            if created:
                dedup.register(spot, known)
                if key:
                    known.ext_ids.add(key)
                inserted += 1
            else:
                skipped += 1
        except Exception as exc:
            conn.rollback()
            dbmod.log_error(conn, run_id, source.key, "db", str(exc))
            errors += 1

    # Deletion detection for full-snapshot sources (12): hide items no longer present.
    if getattr(source, "prunes", False) and fetched > 0:
        try:
            pruned = dbmod.prune_missing(conn, source.key, seen_ext)
        except Exception as exc:
            conn.rollback()
            dbmod.log_error(conn, run_id, source.key, "db", f"prune: {exc}")
            errors += 1

    dbmod.finish_run(conn, run_id, status="success", fetched=fetched, inserted=inserted,
                     skipped=skipped, error_count=errors, updated=updated, pruned=pruned)
    return {"source": source.key, "status": "success", "fetched": fetched, "inserted": inserted,
            "updated": updated, "skipped": skipped, "pruned": pruned, "errors": errors}


def _run_event_source(conn, source, source_id, run_id, pref_map) -> dict:
    """Collect an events source into the events table."""
    fetched = inserted = updated = skipped = errors = 0
    try:
        records = source.fetch()
    except Exception as exc:
        dbmod.log_error(conn, run_id, source.key, "fetch", str(exc))
        dbmod.finish_run(conn, run_id, status="failed", fetched=0, inserted=0, skipped=0, error_count=1)
        return {"source": source.key, "status": "failed", "inserted": 0, "errors": 1}

    for etype, msg in getattr(source, "errors", []):
        dbmod.log_error(conn, run_id, source.key, etype, msg)
        errors += 1

    for rec in records:
        fetched += 1
        if not rec.name:
            skipped += 1
            continue
        try:
            res = dbmod.upsert_event(conn, rec, source_id=source_id, tier=source.tier, pref_map=pref_map)
            inserted += 1 if res == "inserted" else 0
            updated += 1 if res == "updated" else 0
            skipped += 1 if res == "locked" else 0
        except Exception as exc:
            conn.rollback()
            dbmod.log_error(conn, run_id, source.key, "db", str(exc))
            errors += 1

    dbmod.finish_run(conn, run_id, status="success", fetched=fetched, inserted=inserted,
                     skipped=skipped, error_count=errors, updated=updated, pruned=0)
    return {"source": source.key, "status": "success", "fetched": fetched, "inserted": inserted,
            "updated": updated, "skipped": skipped, "pruned": 0, "errors": errors}


def main() -> int:
    conn = dbmod.connect()
    try:
        pref_map = dbmod.prefecture_map(conn)
        known = dbmod.load_known_keys(conn)
        results = []
        for source in build_sources():
            res = run_source(conn, source, pref_map, known)
            results.append(res)
            print(f"[collector] {res}", flush=True)
        total_inserted = sum(r.get("inserted", 0) for r in results)
        total_updated = sum(r.get("updated", 0) for r in results)
        total_pruned = sum(r.get("pruned", 0) for r in results)
        print(f"[collector] done. inserted={total_inserted} updated={total_updated} "
              f"pruned={total_pruned}", flush=True)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
