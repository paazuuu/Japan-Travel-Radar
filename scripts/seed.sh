#!/usr/bin/env bash
# Load MVP1 Kansai seed data into the running postgres container.
# Usage: ./scripts/seed.sh   (run from repo root; requires docker compose stack up)
set -euo pipefail

cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a

: "${POSTGRES_USER:?set POSTGRES_USER (e.g. via .env)}"
: "${POSTGRES_DB:?set POSTGRES_DB (e.g. via .env)}"

echo "==> Applying core schema (0002) + Kansai seed"
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    < database/migrations/0002_core_schema.sql
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    < database/seeds/seed_kansai.sql

echo "==> Row counts:"
docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "SELECT 'spots' t, count(*) FROM spots UNION ALL SELECT 'restaurants', count(*) FROM restaurants;"
