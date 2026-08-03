from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from lumina.business_ops.connectors.erpnext import build_connector_manifest as build_erpnext_manifest
from lumina.business_ops.connectors.odoo import build_connector_manifest as build_odoo_manifest


REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILES_PATH = REPO_ROOT / "model-packs" / "business-ops" / "cfg" / "service-vertical-profiles.yaml"


@pytest.mark.unit
def test_service_vertical_profiles_contract_scaffold_is_present() -> None:
    data = yaml.safe_load(PROFILES_PATH.read_text(encoding="utf-8"))

    assert data["schema_version"] == "1.0.0"
    assert data["mapping_boundary_rules"]["reject_profile_keys_from_canonical_payload"] is True

    profiles = data["profiles"]
    assert set(profiles.keys()) >= {"towing", "retail_delivery"}


@pytest.mark.unit
def test_profile_action_classes_match_generic_service_core() -> None:
    data = yaml.safe_load(PROFILES_PATH.read_text(encoding="utf-8"))
    expected_actions = ["query", "create_draft", "update_draft", "request_commit"]

    for profile_name in ("towing", "retail_delivery"):
        profile = data["profiles"][profile_name]
        assert profile["canonical_capability_namespace"] == "service/work-order"
        assert profile["canonical_action_classes"] == expected_actions


@pytest.mark.unit
def test_provider_manifests_support_service_core_actions() -> None:
    expected_actions = ("query", "create_draft", "update_draft", "request_commit")

    for manifest_builder in (build_erpnext_manifest, build_odoo_manifest):
        manifest = manifest_builder()
        capabilities = {c["namespace"]: tuple(c["supported_actions"]) for c in manifest["capabilities"]}  # type: ignore[index]
        assert capabilities["service/work-order"] == expected_actions
