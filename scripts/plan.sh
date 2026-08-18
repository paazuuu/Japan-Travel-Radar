#!/usr/bin/env bash
# MVP6: generate the reference plan (大阪発・日帰り・5000円・電車・絶景・魚).
set -euo pipefail
cd "$(dirname "$0")/.."

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
echo "==> POST /api/v1/planner/generate"
curl -fsS -X POST "${BACKEND_URL}/api/v1/planner/generate" \
    -H 'Content-Type: application/json' \
    -d '{"origin":"大阪","days":1,"budget":5000,"party_size":2,"transport":"train","purpose":"絶景","food":"魚","max_spots":3}' \
    | python3 -m json.tool
