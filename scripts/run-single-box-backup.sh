#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

ACTION="${1:-backup}"
shift || true

if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source ".venv/bin/activate"
fi

PYTHON="${PYTHON:-python3}"
"$PYTHON" "scripts/single_box_backup_restore.py" "$ACTION" "$@"
