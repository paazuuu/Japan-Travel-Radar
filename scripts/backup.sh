#!/usr/bin/env bash
# Feature B: PostgreSQL backup (15: daily dump / restore test).
# Usage: ./scripts/backup.sh [backup|restore <file>]
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a
PGUSER="${POSTGRES_USER:-travel}"
PGDB="${POSTGRES_DB:-japan_travel}"
OUT_DIR="backups"
mkdir -p "$OUT_DIR"

cmd="${1:-backup}"
case "$cmd" in
  backup)
    ts="$(date +%Y%m%d-%H%M%S)"
    file="$OUT_DIR/${PGDB}-${ts}.sql.gz"
    echo "==> Dumping to $file"
    docker compose exec -T postgres pg_dump -U "$PGUSER" -d "$PGDB" | gzip > "$file"
    echo "==> Done ($(du -h "$file" | cut -f1))"
    # retain the 14 most recent dumps
    ls -1t "$OUT_DIR"/${PGDB}-*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm -f
    ;;
  restore)
    file="${2:?usage: ./scripts/backup.sh restore <file.sql.gz>}"
    echo "==> Restoring $file into $PGDB"
    gunzip -c "$file" | docker compose exec -T postgres psql -U "$PGUSER" -d "$PGDB"
    echo "==> Restore complete"
    ;;
  *)
    echo "usage: $0 [backup|restore <file>]" >&2; exit 1 ;;
esac
