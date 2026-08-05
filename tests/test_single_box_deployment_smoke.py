from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = REPO_ROOT / "scripts" / "single_box_health_check.py"


@pytest.fixture(scope="module")
def checker_module():
    spec = importlib.util.spec_from_file_location("single_box_health_check", _SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_runtime(tmp_path: Path, *, include_missing_required: bool = False) -> Path:
    domain_physics = tmp_path / "domain-physics.json"
    subject_profile = tmp_path / "subject.yaml"
    base_profile = tmp_path / "base.yaml"
    domain_ext = tmp_path / "domain-ext.yaml"

    domain_physics.write_text("{}\n", encoding="utf-8")
    subject_profile.write_text("{}\n", encoding="utf-8")
    base_profile.write_text("{}\n", encoding="utf-8")
    domain_ext.write_text("{}\n", encoding="utf-8")

    runtime = {
        "runtime": {
            "domain_physics_path": str(domain_physics),
            "subject_profile_path": str(subject_profile),
            "base_profile_path": str(base_profile),
            "domain_profile_extension_path": str(domain_ext),
        }
    }
    if include_missing_required:
        runtime["runtime"]["domain_physics_path"] = str(tmp_path / "missing-domain-physics.json")

    runtime_path = tmp_path / "runtime-config.yaml"
    runtime_path.write_text(yaml.safe_dump(runtime), encoding="utf-8")
    return runtime_path


def _write_connector_registry(tmp_path: Path, statuses: list[str]) -> Path:
    entries = []
    for idx, status in enumerate(statuses, start=1):
        entries.append(
            {
                "organization_id": "org-a",
                "site_id": "site-a",
                "connector_instance_id": f"conn-{idx}",
                "health_status": status,
            }
        )
    path = tmp_path / "connector-registry.json"
    path.write_text(json.dumps({"connector_registry_entries": entries}), encoding="utf-8")
    return path


def test_report_healthy_when_required_paths_and_connectors_are_healthy(tmp_path: Path, checker_module):
    runtime_path = _write_runtime(tmp_path)
    connector_path = _write_connector_registry(tmp_path, ["healthy", "healthy"])

    for rel in ("data/profiles", "data/retrieval-index", "data/knowledge-index"):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)

    report = checker_module.build_single_box_health_report(
        repo_root=tmp_path,
        runtime_config_path=runtime_path,
        connector_registry_path=connector_path,
    )

    assert report["status"] == "healthy"
    assert len(report["runtime"]["checks"]) == 4
    assert len(report["connectors"]["checks"]) == 2


def test_report_degraded_when_connector_is_degraded(tmp_path: Path, checker_module):
    runtime_path = _write_runtime(tmp_path)
    connector_path = _write_connector_registry(tmp_path, ["healthy", "degraded"])

    for rel in ("data/profiles", "data/retrieval-index", "data/knowledge-index"):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)

    report = checker_module.build_single_box_health_report(
        repo_root=tmp_path,
        runtime_config_path=runtime_path,
        connector_registry_path=connector_path,
    )

    assert report["status"] == "degraded"


def test_report_unhealthy_when_required_runtime_path_missing(tmp_path: Path, checker_module):
    runtime_path = _write_runtime(tmp_path, include_missing_required=True)

    for rel in ("data/profiles", "data/retrieval-index", "data/knowledge-index"):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)

    report = checker_module.build_single_box_health_report(
        repo_root=tmp_path,
        runtime_config_path=runtime_path,
        connector_registry_path=None,
    )

    assert report["status"] == "unhealthy"


def test_report_unhealthy_when_connector_health_status_is_unhealthy(tmp_path: Path, checker_module):
    runtime_path = _write_runtime(tmp_path)
    connector_path = _write_connector_registry(tmp_path, ["unhealthy"])

    for rel in ("data/profiles", "data/retrieval-index", "data/knowledge-index"):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)

    report = checker_module.build_single_box_health_report(
        repo_root=tmp_path,
        runtime_config_path=runtime_path,
        connector_registry_path=connector_path,
    )

    assert report["status"] == "unhealthy"
