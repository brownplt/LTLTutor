#!/bin/bash
set -e

# Run Playwright E2E tests against a running LTL Tutor instance.
#
# Usage:
#   ./run_e2e.sh                         # test against localhost:5000
#   BASE_URL=http://app:5000 ./run_e2e.sh  # test against a docker service
#   docker compose run e2e               # run via docker compose (preferred)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/e2e"

BASE_URL="${BASE_URL:-http://localhost:5000}"
export BASE_URL

echo "Running E2E tests against $BASE_URL ..."
python -m pytest -v "$@"
