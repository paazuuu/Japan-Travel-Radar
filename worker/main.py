"""Worker service entrypoint: runs AI analysis (MVP3) and, later, ranking (MVP4).

Modes:
  RUN_MODE=once      -> run the pending jobs a single time and exit
  RUN_MODE=schedule  -> run, then repeat every WORKER_INTERVAL_SECONDS
"""

import os
import time

import db as dbmod
from analyzer import analyze


def run_analysis_once() -> int:
    conn = dbmod.connect()
    analyzed = 0
    try:
        spots = dbmod.fetch_spots_needing_analysis(conn)
        for spot_id, name, description, category in spots:
            result = analyze(name, description, category)
            dbmod.upsert_analysis(conn, spot_id, result)
            analyzed += 1
        print(f"[worker] analysis done. analyzed={analyzed}", flush=True)
        return analyzed
    finally:
        conn.close()


def main() -> None:
    mode = os.environ.get("RUN_MODE", "schedule")
    interval = int(os.environ.get("WORKER_INTERVAL_SECONDS", str(3600)))

    if mode == "once":
        run_analysis_once()
        return

    while True:
        try:
            run_analysis_once()
        except Exception as exc:
            print(f"[worker] analysis failed: {exc}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
