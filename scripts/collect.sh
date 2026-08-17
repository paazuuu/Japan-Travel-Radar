#!/usr/bin/env bash
# Run the collector pipeline once against the running stack (MVP2 daily job).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Running collector once"
docker compose run --rm -e RUN_MODE=once collector

echo "==> Latest collector runs:"
# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a
docker compose exec -T postgres psql -U "${POSTGRES_USER:-travel}" -d "${POSTGRES_DB:-japan_travel}" -c \
    "SELECT source_key, status, fetched, inserted, skipped, error_count FROM collector_runs ORDER BY started_at DESC LIMIT 10;"
