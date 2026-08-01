"""Tests for module-map routing in the active business-ops pack.

Covers:
    1. runtime-config has a module_map entry for the active module ID
    2. module-config sidecar merge exposes domain_physics_path
    3. Referenced domain-physics file exists and has expected identity fields
    4. Module-selection logic resolves module_map overrides correctly
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_CFG = REPO_ROOT / "model-packs" / "business-ops" / "cfg" / "runtime-config.yaml"

_ACTIVE_MODULE_ID = "domain/bizops/auto-repair/v1"
_ACTIVE_MODULE_DIR = REPO_ROOT / "model-packs" / "business-ops" / "modules" / "auto-repair"

_EXPECTED_DOMAIN_PHYSICS_PATH = "model-packs/business-ops/modules/auto-repair/domain-physics.json"




# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def runtime_cfg() -> dict:
    with open(RUNTIME_CFG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["runtime"]


@pytest.fixture(scope="module")
def module_map(runtime_cfg) -> dict:
    raw = runtime_cfg.get("module_map", {})
    # Replicate the runtime-loader sidecar merge so tests see the full
    # module config even when entries use module_path stubs.
    for _mod_id, _mod_cfg in raw.items():
        _mod_dir = _mod_cfg.get("module_path")
        if _mod_dir:
            _mc_path = REPO_ROOT / _mod_dir / "module-config.yaml"
            if _mc_path.is_file():
                with open(_mc_path, encoding="utf-8") as f:
                    _mc = yaml.safe_load(f)
                if isinstance(_mc, dict):
                    for _k, _v in _mc.items():
                        if _k not in _mod_cfg:
                            _mod_cfg[_k] = _v
    return raw


# ---------------------------------------------------------------------------
# Module-map structure
# ---------------------------------------------------------------------------

class TestModuleMapStructure:
    def test_module_map_key_exists(self, runtime_cfg):
        assert "module_map" in runtime_cfg, (
            "runtime-config.yaml missing 'module_map' under runtime:"
        )

    def test_module_map_has_active_entry(self, module_map):
        assert _ACTIVE_MODULE_ID in module_map

    def test_active_entry_has_domain_physics_path(self, module_map):
        entry = module_map[_ACTIVE_MODULE_ID]
        assert "domain_physics_path" in entry, (
            f"module_map[{_ACTIVE_MODULE_ID!r}] missing 'domain_physics_path'"
        )
        assert isinstance(entry["domain_physics_path"], str)
        assert entry["domain_physics_path"].strip()


# ---------------------------------------------------------------------------
# Domain-physics files referenced by module_map exist and parse
# ---------------------------------------------------------------------------

class TestModuleMapPhysicsPaths:
    def test_domain_physics_path_file_exists(self, module_map):
        path_str = module_map[_ACTIVE_MODULE_ID]["domain_physics_path"]
        path = REPO_ROOT / path_str
        assert path.exists(), f"{path_str} does not exist (referenced by module_map[{_ACTIVE_MODULE_ID!r}])"

    def test_domain_physics_json_is_valid(self, module_map):
        path_str = module_map[_ACTIVE_MODULE_ID]["domain_physics_path"]
        path = REPO_ROOT / path_str
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), f"{path_str} did not load as a JSON object"
        assert data.get("id") == _ACTIVE_MODULE_ID
        assert data.get("department") == "Operations"


# ---------------------------------------------------------------------------
# Module sidecar and module artifact checks
# ---------------------------------------------------------------------------

class TestModuleArtifacts:
    def test_module_config_exists(self):
        assert (_ACTIVE_MODULE_DIR / "module-config.yaml").exists()

    def test_module_config_domain_physics_path_matches_runtime(self, module_map):
        assert module_map[_ACTIVE_MODULE_ID]["domain_physics_path"] == _EXPECTED_DOMAIN_PHYSICS_PATH

    def test_domain_physics_declares_risk_invariants(self, module_map):
        physics_path = REPO_ROOT / module_map[_ACTIVE_MODULE_ID]["domain_physics_path"]
        with open(physics_path, encoding="utf-8") as f:
            data = json.load(f)
        invariants = data.get("invariants") or []
        invariant_ids = {inv.get("id") for inv in invariants if isinstance(inv, dict)}
        assert "high_risk_requires_approval" in invariant_ids
        assert "mutation_must_be_staged" in invariant_ids

    def test_domain_physics_declares_standing_orders(self, module_map):
        physics_path = REPO_ROOT / module_map[_ACTIVE_MODULE_ID]["domain_physics_path"]
        with open(physics_path, encoding="utf-8") as f:
            data = json.load(f)
        so_ids = {so.get("id") for so in (data.get("standing_orders") or []) if isinstance(so, dict)}
        assert "recommend_next_step" in so_ids
        assert "stage_draft_only" in so_ids
        assert "escalate_to_manager" in so_ids

    def test_module_sidecar_exposes_connector_allowlist_defaults(self, module_map):
        entry = module_map[_ACTIVE_MODULE_ID]
        allowlist = entry.get("connector_allowlist_defaults") or {}
        assert "service/work-order" in (allowlist.get("capabilities") or [])
        assert "query" in (allowlist.get("action_classes") or [])
        assert "update_draft" in (allowlist.get("action_classes") or [])

    def test_module_sidecar_exposes_confidence_profile_defaults(self, module_map):
        entry = module_map[_ACTIVE_MODULE_ID]
        profile = entry.get("confidence_profile_defaults") or {}
        assert float(profile.get("suggest_threshold", 0)) >= 0.0
        assert float(profile.get("confirmation_threshold", 0)) >= 0.0


# ---------------------------------------------------------------------------
# Module routing logic
# ---------------------------------------------------------------------------

class TestModuleRoutingLogic:
    """Verify the module-selection logic: module_map lookup overrides static default."""

    def _resolve_domain_physics_path(
        self, runtime: dict, profile: dict
    ) -> str:
        """Replicate the routing logic from _build_domain_context in server.py."""
        default_path = runtime["domain_physics_path"]
        module_map = runtime.get("module_map") or {}
        domain_id = profile.get("domain_id") or profile.get("subject_domain_id")
        if domain_id and domain_id in module_map:
            return module_map[domain_id]["domain_physics_path"]
        return default_path

    def test_no_domain_id_uses_static_default(self, runtime_cfg):
        profile = {}
        result = self._resolve_domain_physics_path(runtime_cfg, profile)
        assert result == runtime_cfg["domain_physics_path"]

    def test_unknown_domain_id_uses_static_default(self, runtime_cfg):
        profile = {"domain_id": "domain/bizops/unknown/v1"}
        result = self._resolve_domain_physics_path(runtime_cfg, profile)
        assert result == runtime_cfg["domain_physics_path"]

    def test_known_domain_id_routes_to_module_path(self, runtime_cfg, module_map):
        domain_id = _ACTIVE_MODULE_ID
        profile = {"domain_id": domain_id}
        result = self._resolve_domain_physics_path(runtime_cfg, profile)
        expected = module_map[domain_id]["domain_physics_path"]
        assert result == expected, (
            f"Routing failed for {domain_id!r}: got {result!r}, expected {expected!r}"
        )

    def test_primary_module_routes_to_auto_repair_physics(self, runtime_cfg):
        profile = {"domain_id": _ACTIVE_MODULE_ID}
        result = self._resolve_domain_physics_path(runtime_cfg, profile)
        assert "auto-repair" in result

    def test_subject_domain_id_fallback_key(self, runtime_cfg):
        # Support alternative key name used in some profile templates
        profile = {"subject_domain_id": _ACTIVE_MODULE_ID}
        result = self._resolve_domain_physics_path(runtime_cfg, profile)
        assert "auto-repair" in result
