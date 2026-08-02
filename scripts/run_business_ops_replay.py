"""Run deterministic business-ops fixture replay and emit CI evidence JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


_REPO_ROOT = _default_repo_root()
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lumina.business_ops.replay import generate_replay_report


def main() -> int:
    repo = _default_repo_root()
    parser = argparse.ArgumentParser(description="Replay business-ops fixture for CI evidence")
    parser.add_argument(
        "--fixture",
        default=str(repo / "examples" / "business-ops-auto-repair-e2e-fixture.json"),
        help="Path to fixture JSON",
    )
    parser.add_argument(
        "--thread-policy",
        default=str(repo / "model-packs" / "business-ops" / "cfg" / "thread-routing-policy.yaml"),
        help="Path to thread routing policy YAML",
    )
    parser.add_argument(
        "--decision-policy",
        default=str(repo / "model-packs" / "business-ops" / "cfg" / "decision-precedent-policy.yaml"),
        help="Path to decision precedent policy YAML",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional path to write JSON report; prints to stdout when omitted",
    )
    args = parser.parse_args()

    report = generate_replay_report(
        args.fixture,
        thread_policy_path=args.thread_policy,
        decision_policy_path=args.decision_policy,
    )

    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
        print(f"[OK] business-ops replay report written to {out_path}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
