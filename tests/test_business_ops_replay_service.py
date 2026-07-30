"""Tests for business-ops deterministic replay service and CLI script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from lumina.business_ops.replay import generate_replay_report


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "examples" / "business-ops-auto-repair-e2e-fixture.json"
THREAD_POLICY = REPO_ROOT / "model-packs" / "business-ops" / "cfg" / "thread-routing-policy.yaml"
DECISION_POLICY = REPO_ROOT / "model-packs" / "business-ops" / "cfg" / "decision-precedent-policy.yaml"
SCRIPT = REPO_ROOT / "scripts" / "run_business_ops_replay.py"


@pytest.mark.unit
def test_generate_replay_report_matches_fixture_expectations() -> None:
    report = generate_replay_report(
        FIXTURE,
        thread_policy_path=THREAD_POLICY,
        decision_policy_path=DECISION_POLICY,
    )

    assert report["schema_version"] == "1.0.0"
    assert report["fixture_id"] == "business-ops-auto-repair-e2e-v1"
    assert all(report["thread_routing"]["matches_expected"].values())
    assert all(report["decision_precedent"]["matches_expected"].values())
    assert all(report["connector_resolution"]["matches_expected"].values())


@pytest.mark.unit
def test_replay_script_writes_report_file(tmp_path: Path) -> None:
    out = tmp_path / "business-ops-replay-report.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--fixture",
            str(FIXTURE),
            "--thread-policy",
            str(THREAD_POLICY),
            "--decision-policy",
            str(DECISION_POLICY),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )

    assert proc.returncode == 0, proc.stderr
    assert out.exists()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["fixture_id"] == "business-ops-auto-repair-e2e-v1"
    assert payload["thread_routing"]["record"]["decision"] == "attach_existing"
