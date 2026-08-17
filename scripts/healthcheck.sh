#!/usr/bin/env bash
# Quick MVP0 verification: backend health + PostGIS.
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "==> Checking backend health at ${BACKEND_URL}/health"
curl -fsS "${BACKEND_URL}/health" | tee /dev/stderr | grep -q '"status"'

echo
echo "==> Done. If status is 'ok', DB + PostGIS are reachable."
