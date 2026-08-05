#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3}"
if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source ".venv/bin/activate"
fi

"$PYTHON" "$SCRIPT_DIR/single_box_health_check.py" \
  --runtime-config "model-packs/business-ops/cfg/runtime-config.yaml" \
  --json-out "data/staging/single-box-health-report.json" \
  --fail-on-degraded
