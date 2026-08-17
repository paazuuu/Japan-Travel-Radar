#!/usr/bin/env bash
# MVP4: load demo observations, compute trend scores, show the rising ranking.
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
[ -f .env ] && set -a && . ./.env && set +a
PSQL=(docker compose exec -T postgres psql -U "${POSTGRES_USER:-travel}" -d "${POSTGRES_DB:-japan_travel}")

echo "==> Seeding demo observations"
"${PSQL[@]}" < database/seeds/seed_observations.sql

echo "==> Running worker (analysis + ranking) once"
docker compose run --rm -e RUN_MODE=once worker

echo "==> 急上昇 (top growth) today:"
"${PSQL[@]}" -c "
  SELECT s.name, t.trend_score, t.growth_score, t.is_reference
  FROM trend_scores t JOIN spots s ON s.id = t.spot_id
  WHERE t.score_date = (SELECT max(score_date) FROM trend_scores)
  ORDER BY t.growth_score DESC LIMIT 10;"
