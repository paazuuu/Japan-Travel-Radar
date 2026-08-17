#!/usr/bin/env bash
# Apply all database/migrations/*.sql in order (idempotent; safe to re-run).
# On a fresh volume Postgres auto-runs these via docker-entrypoint-initdb.d;
# use this to apply new migrations to an already-initialized database.
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a
PSQL=(docker compose exec -T postgres psql -v ON_ERROR_STOP=1 \
    -U "${POSTGRES_USER:-travel}" -d "${POSTGRES_DB:-japan_travel}")

for f in database/migrations/*.sql; do
    echo "==> Applying $f"
    "${PSQL[@]}" < "$f"
done
echo "==> Migrations applied."
