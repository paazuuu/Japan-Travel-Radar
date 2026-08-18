#!/usr/bin/env bash
# Run the AI analysis worker once over spots that need analysis (MVP3).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Running analysis worker once"
docker compose run --rm -e RUN_MODE=once worker

# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a
docker compose exec -T postgres psql -U "${POSTGRES_USER:-travel}" -d "${POSTGRES_DB:-japan_travel}" -c \
    "SELECT count(*) AS analyses, round(avg(confidence),2) AS avg_conf FROM spot_analyses;"
