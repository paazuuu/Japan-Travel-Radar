"""Collector service entrypoint (MVP0 skeleton).

Real collection logic arrives in MVP2 (04_MVP2_COLLECTOR.md). For MVP0 this
just verifies the container builds and can reach PostgreSQL, then idles so the
compose stack stays healthy.
"""

import os
import time


def main() -> None:
    db_url = os.environ.get("DATABASE_URL", "<unset>")
    print(f"[collector] started. DATABASE_URL={db_url}", flush=True)
    print("[collector] MVP0 skeleton — no sources configured yet.", flush=True)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
