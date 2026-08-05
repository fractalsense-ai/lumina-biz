#!/usr/bin/env python3
"""Single-box pilot readiness checklist validator.

Consumes smoke/health output and backup artifacts to produce a deterministic
readiness checklist report suitable for pilot-go/no-go reviews.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _to_abs(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _count_backups(backups_dir: Path) -> int:
    return len([p for p in backups_dir.glob("single-box-backup-*.zip") if p.is_file()])


def evaluate_readiness(
    *,
    repo_root: Path,
    health_report_path: Path,
    backups_dir: Path,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    health_payload: dict[str, Any] | None = None
    health_status = "missing"
    health_profile = "missing"
    if health_report_path.exists():
        try:
            health_payload = json.loads(health_report_path.read_text(encoding="utf-8"))
            if isinstance(health_payload, dict):
                health_profile = str(health_payload.get("profile", "missing")).strip().lower()
                if health_profile == "single-box-v1":
                    health_status = str(health_payload.get("status", "missing")).strip().lower()
                else:
                    health_status = "invalid"
            else:
                health_status = "invalid"
                health_profile = "invalid"
        except Exception:
            health_status = "invalid"
            health_profile = "invalid"

    checks.append(
        {
            "id": "health_report_present",
            "description": "single-box smoke report exists",
            "passed": health_report_path.exists(),
            "details": str(health_report_path),
        }
    )

    checks.append(
        {
            "id": "health_profile_single_box",
            "description": "health report profile is single-box-v1",
            "passed": health_profile == "single-box-v1",
            "details": health_profile,
        }
    )

    checks.append(
        {
            "id": "health_status_healthy",
            "description": "single-box health status is healthy",
            "passed": health_status == "healthy",
            "details": health_status,
        }
    )

    backup_count = _count_backups(backups_dir)
    checks.append(
        {
            "id": "backup_archive_present",
            "description": "at least one backup archive exists",
            "passed": backup_count >= 1,
            "details": {
                "backup_count": backup_count,
                "backups_dir": str(backups_dir),
            },
        }
    )

    runbook_paths = [
        repo_root / "docs" / "8-admin" / "single-box-deployment-profile.md",
        repo_root / "docs" / "8-admin" / "single-box-backup-restore-retention.md",
        repo_root / "docs" / "8-admin" / "single-box-operator-runbooks.md",
    ]
    runbooks_present = all(path.exists() for path in runbook_paths)
    checks.append(
        {
            "id": "runbooks_present",
            "description": "required single-box runbooks are present",
            "passed": runbooks_present,
            "details": [str(path) for path in runbook_paths],
        }
    )

    checklist_passed = all(bool(item.get("passed")) for item in checks)
    return {
        "schema_version": "1.0.0",
        "profile": "single-box-v1",
        "evaluated_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "pass" if checklist_passed else "fail",
        "checks": checks,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate single-box pilot readiness")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root path",
    )
    parser.add_argument(
        "--health-report",
        type=Path,
        default=Path("data/staging/single-box-health-report.json"),
        help="Path to single-box health report JSON",
    )
    parser.add_argument(
        "--backups-dir",
        type=Path,
        default=Path("data/staging/backups"),
        help="Path to backup archive directory",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional output path for readiness JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()

    report = evaluate_readiness(
        repo_root=repo_root,
        health_report_path=_to_abs(repo_root, args.health_report),
        backups_dir=_to_abs(repo_root, args.backups_dir),
    )

    rendered = json.dumps(report, indent=2, ensure_ascii=True)
    if args.json_out is not None:
        out_path = _to_abs(repo_root, args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)

    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
