"""Worker service entrypoint (MVP0 skeleton).

Background jobs (normalization, AI analysis, ranking) are added from MVP2
onward. For MVP0 this is a healthy idle process so the compose stack is
complete and reproducible.
"""

import os
import time


def main() -> None:
    db_url = os.environ.get("DATABASE_URL", "<unset>")
    print(f"[worker] started. DATABASE_URL={db_url}", flush=True)
    print("[worker] MVP0 skeleton — no jobs scheduled yet.", flush=True)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
