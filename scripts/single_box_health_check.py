#!/usr/bin/env python3
"""Deterministic single-box deployment health and smoke checks.

This tool validates a local-first "single-box" profile by checking:
- required runtime-config paths used by the active domain pack
- local institutional-memory directories
- optional connector registry health statuses

It emits a JSON report and exits non-zero when the profile is unhealthy.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

_HEALTH_ORDER = {"healthy": 0, "degraded": 1, "unhealthy": 2}
_ALLOWED_CONNECTOR_STATUSES = {"healthy", "degraded", "unhealthy"}
_REQUIRED_RUNTIME_KEYS = (
    "domain_physics_path",
    "subject_profile_path",
    "base_profile_path",
    "domain_profile_extension_path",
)
_OPTIONAL_MEMORY_DIRS = (
    "data/profiles",
    "data/retrieval-index",
    "data/knowledge-index",
)


def _abs(repo_root: Path, rel_or_abs: str) -> Path:
    path = Path(rel_or_abs)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _normalize_connector_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        entries = payload.get("connector_registry_entries")
        if isinstance(entries, list):
            return [item for item in entries if isinstance(item, dict)]
    return []


def _combine_status(values: list[str]) -> str:
    worst = "healthy"
    for value in values:
        if _HEALTH_ORDER.get(value, 2) > _HEALTH_ORDER[worst]:
            worst = value
    return worst


def build_single_box_health_report(
    *,
    repo_root: Path,
    runtime_config_path: Path,
    connector_registry_path: Path | None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "profile": "single-box-v1",
        "checked_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "healthy",
        "runtime": {"runtime_config_path": str(runtime_config_path), "checks": []},
        "memory": {"checks": []},
        "connectors": {"source": str(connector_registry_path) if connector_registry_path else None, "checks": []},
    }

    statuses: list[str] = []

    runtime: dict[str, Any] = {}
    try:
        with open(runtime_config_path, encoding="utf-8") as fh:
            runtime_config = yaml.safe_load(fh) or {}
        if not isinstance(runtime_config, dict):
            raise TypeError("runtime config must deserialize to a mapping")
        runtime_obj = runtime_config.get("runtime") or {}
        if not isinstance(runtime_obj, dict):
            raise TypeError("runtime config field 'runtime' must be a mapping")
        runtime = runtime_obj
    except Exception as exc:
        report["runtime"]["config_error"] = str(exc)
        statuses.append("unhealthy")

    for key in _REQUIRED_RUNTIME_KEYS:
        raw_path = runtime.get(key)
        exists = isinstance(raw_path, str) and _abs(repo_root, raw_path).exists()
        check_status = "healthy" if exists else "unhealthy"
        report["runtime"]["checks"].append(
            {
                "name": key,
                "path": str(raw_path) if isinstance(raw_path, str) else None,
                "exists": exists,
                "status": check_status,
            }
        )
        statuses.append(check_status)

    for rel_path in _OPTIONAL_MEMORY_DIRS:
        abs_path = _abs(repo_root, rel_path)
        exists = abs_path.exists()
        check_status = "healthy" if exists else "degraded"
        report["memory"]["checks"].append(
            {
                "name": rel_path,
                "path": str(abs_path),
                "exists": exists,
                "status": check_status,
            }
        )
        statuses.append(check_status)

    connector_entries: list[dict[str, Any]] = []
    if connector_registry_path is not None and connector_registry_path.exists():
        try:
            with open(connector_registry_path, encoding="utf-8") as fh:
                payload = json.load(fh)
            connector_entries = _normalize_connector_entries(payload)
        except Exception as exc:
            report["connectors"]["parse_error"] = str(exc)
            statuses.append("degraded")

    for entry in connector_entries:
        raw_status = str(entry.get("health_status", "unhealthy")).strip().lower()
        status = raw_status if raw_status in _ALLOWED_CONNECTOR_STATUSES else "unhealthy"
        report["connectors"]["checks"].append(
            {
                "connector_instance_id": str(entry.get("connector_instance_id", "unknown")),
                "organization_id": str(entry.get("organization_id", "")),
                "site_id": str(entry.get("site_id", "")),
                "health_status": status,
            }
        )
        statuses.append(status)

    report["status"] = _combine_status(statuses)
    report["summary"] = {
        "runtime_checks": len(report["runtime"]["checks"]),
        "memory_checks": len(report["memory"]["checks"]),
        "connector_checks": len(report["connectors"]["checks"]),
    }
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-box deployment health and smoke checks")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to parent of scripts/)",
    )
    parser.add_argument(
        "--runtime-config",
        type=Path,
        default=Path("model-packs/business-ops/cfg/runtime-config.yaml"),
        help="Runtime config path (absolute or repo-relative)",
    )
    parser.add_argument(
        "--connector-registry",
        type=Path,
        default=None,
        help="Optional connector registry JSON payload path",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional output file path for the JSON report",
    )
    parser.add_argument(
        "--fail-on-degraded",
        action="store_true",
        help="Exit non-zero for degraded status (default only fails on unhealthy)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()
    runtime_config_path = _abs(repo_root, str(args.runtime_config)).resolve()
    connector_registry_path = None
    if args.connector_registry is not None:
        connector_registry_path = _abs(repo_root, str(args.connector_registry)).resolve()

    try:
        report = build_single_box_health_report(
            repo_root=repo_root,
            runtime_config_path=runtime_config_path,
            connector_registry_path=connector_registry_path,
        )
    except Exception as exc:
        report = {
            "profile": "single-box-v1",
            "checked_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "status": "unhealthy",
            "runtime": {"runtime_config_path": str(runtime_config_path), "checks": []},
            "memory": {"checks": []},
            "connectors": {"source": str(connector_registry_path) if connector_registry_path else None, "checks": []},
            "error": str(exc),
            "summary": {"runtime_checks": 0, "memory_checks": 0, "connector_checks": 0},
        }

    rendered = json.dumps(report, indent=2, ensure_ascii=True)
    if args.json_out is not None:
        out_path = _abs(repo_root, str(args.json_out)).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)

    status = report["status"]
    if status == "unhealthy":
        return 2
    if status == "degraded" and args.fail_on_degraded:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
