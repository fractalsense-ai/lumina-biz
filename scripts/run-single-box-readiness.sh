#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source ".venv/bin/activate"
fi

PYTHON="${PYTHON:-python3}"
"$PYTHON" "scripts/single_box_readiness_check.py" \
  --health-report "data/staging/single-box-health-report.json" \
  --backups-dir "data/staging/backups" \
  --json-out "data/staging/single-box-readiness-report.json"
