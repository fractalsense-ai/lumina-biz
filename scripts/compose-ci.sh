#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-backend}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.test.yml}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

case "$TARGET" in
  backend|frontend-unit|frontend-e2e)
    echo "Running compose CI workflow for service '$TARGET'..."
    docker compose -f "$COMPOSE_FILE" run --rm "$TARGET"
    ;;
  all)
    echo "Running full compose CI workflow (all services)..."
    docker compose -f "$COMPOSE_FILE" up --abort-on-container-exit --exit-code-from backend
    ;;
  *)
    echo "Unknown target '$TARGET'. Use: backend | frontend-unit | frontend-e2e | all" >&2
    exit 1
    ;;
esac

echo "Compose CI workflow passed for target '$TARGET'."
