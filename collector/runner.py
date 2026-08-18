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

    fetched = inserted = skipped = errors = 0
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
            if dedup.is_duplicate(spot, known):
                skipped += 1
                continue
            ok, status, verr = validate(spot)
            if not ok:
                dbmod.log_error(conn, run_id, source.key, "validation", verr or "invalid")
                errors += 1
                continue
            created = dbmod.insert_spot(conn, spot, source_id=source_id, status=status, pref_map=pref_map)
            if created:
                dedup.register(spot, known)
                inserted += 1
            else:
                skipped += 1
        except Exception as exc:
            conn.rollback()
            dbmod.log_error(conn, run_id, source.key, "db", str(exc))
            errors += 1

    status = "success" if errors == 0 else "success"  # partial errors still count as a completed run
    dbmod.finish_run(conn, run_id, status=status, fetched=fetched, inserted=inserted,
                     skipped=skipped, error_count=errors)
    return {"source": source.key, "status": status, "fetched": fetched,
            "inserted": inserted, "skipped": skipped, "errors": errors}


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
        print(f"[collector] done. total inserted={total_inserted}", flush=True)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
