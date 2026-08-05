from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = REPO_ROOT / "scripts" / "single_box_readiness_check.py"


@pytest.fixture(scope="module")
def readiness_mod():
    spec = importlib.util.spec_from_file_location("single_box_readiness_check", _SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_health_report(path: Path, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile": "single-box-v1",
        "checked_utc": "2026-08-05T00:00:00Z",
        "status": status,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _touch_backup(backups_dir: Path, name: str = "single-box-backup-20260805T000000Z.zip") -> None:
    backups_dir.mkdir(parents=True, exist_ok=True)
    (backups_dir / name).write_text("x", encoding="utf-8")


def test_readiness_passes_when_health_healthy_and_backup_present(tmp_path: Path, readiness_mod):
    health_report = tmp_path / "data" / "staging" / "single-box-health-report.json"
    backups_dir = tmp_path / "data" / "staging" / "backups"
    _write_health_report(health_report, "healthy")
    _touch_backup(backups_dir)

    docs_dir = tmp_path / "docs" / "8-admin"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "single-box-deployment-profile.md",
        "single-box-backup-restore-retention.md",
        "single-box-operator-runbooks.md",
    ):
        (docs_dir / name).write_text("ok\n", encoding="utf-8")

    report = readiness_mod.evaluate_readiness(
        repo_root=tmp_path,
        health_report_path=health_report,
        backups_dir=backups_dir,
    )

    assert report["status"] == "pass"
    assert all(bool(check["passed"]) for check in report["checks"])


def test_readiness_fails_when_health_degraded(tmp_path: Path, readiness_mod):
    health_report = tmp_path / "data" / "staging" / "single-box-health-report.json"
    backups_dir = tmp_path / "data" / "staging" / "backups"
    _write_health_report(health_report, "degraded")
    _touch_backup(backups_dir)

    docs_dir = tmp_path / "docs" / "8-admin"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "single-box-deployment-profile.md",
        "single-box-backup-restore-retention.md",
        "single-box-operator-runbooks.md",
    ):
        (docs_dir / name).write_text("ok\n", encoding="utf-8")

    report = readiness_mod.evaluate_readiness(
        repo_root=tmp_path,
        health_report_path=health_report,
        backups_dir=backups_dir,
    )

    assert report["status"] == "fail"
    gate = next(c for c in report["checks"] if c["id"] == "health_status_healthy")
    assert gate["passed"] is False


def test_readiness_fails_when_backup_missing(tmp_path: Path, readiness_mod):
    health_report = tmp_path / "data" / "staging" / "single-box-health-report.json"
    backups_dir = tmp_path / "data" / "staging" / "backups"
    _write_health_report(health_report, "healthy")

    docs_dir = tmp_path / "docs" / "8-admin"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "single-box-deployment-profile.md",
        "single-box-backup-restore-retention.md",
        "single-box-operator-runbooks.md",
    ):
        (docs_dir / name).write_text("ok\n", encoding="utf-8")

    report = readiness_mod.evaluate_readiness(
        repo_root=tmp_path,
        health_report_path=health_report,
        backups_dir=backups_dir,
    )

    assert report["status"] == "fail"
    gate = next(c for c in report["checks"] if c["id"] == "backup_archive_present")
    assert gate["passed"] is False


def test_readiness_fails_when_health_profile_mismatch(tmp_path: Path, readiness_mod):
    health_report = tmp_path / "data" / "staging" / "single-box-health-report.json"
    backups_dir = tmp_path / "data" / "staging" / "backups"
    _write_health_report(health_report, "healthy")
    _touch_backup(backups_dir)

    payload = json.loads(health_report.read_text(encoding="utf-8"))
    payload["profile"] = "not-single-box"
    health_report.write_text(json.dumps(payload), encoding="utf-8")

    docs_dir = tmp_path / "docs" / "8-admin"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "single-box-deployment-profile.md",
        "single-box-backup-restore-retention.md",
        "single-box-operator-runbooks.md",
    ):
        (docs_dir / name).write_text("ok\n", encoding="utf-8")

    report = readiness_mod.evaluate_readiness(
        repo_root=tmp_path,
        health_report_path=health_report,
        backups_dir=backups_dir,
    )

    assert report["status"] == "fail"
    profile_gate = next(c for c in report["checks"] if c["id"] == "health_profile_single_box")
    assert profile_gate["passed"] is False
    status_gate = next(c for c in report["checks"] if c["id"] == "health_status_healthy")
    assert status_gate["passed"] is False
