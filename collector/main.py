"""Collector service entrypoint.

Modes:
  RUN_MODE=once      -> run the pipeline a single time and exit (used by scripts/cron)
  RUN_MODE=schedule  -> run once, then every COLLECT_INTERVAL_SECONDS (default daily)
Default is 'schedule' so the compose service stays up and runs the daily job.
"""

import os
import time

from runner import main as run_once


def main() -> None:
    mode = os.environ.get("RUN_MODE", "schedule")
    interval = int(os.environ.get("COLLECT_INTERVAL_SECONDS", str(24 * 3600)))

    if mode == "once":
        run_once()
        return

    while True:
        try:
            run_once()
        except Exception as exc:  # never let the loop die
            print(f"[collector] run failed: {exc}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
