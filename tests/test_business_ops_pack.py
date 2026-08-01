"""Structural tests for the Business Ops pack scaffold (slice 32)."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from lumina.api.config import _assemble_profile
from lumina.core.permissions import Operation, check_min_tier, check_permission


REPO_ROOT = Path(__file__).resolve().parent.parent
PACK = REPO_ROOT / "model-packs" / "business-ops"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _import_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    saved = sys.modules.get(name)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        if saved is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = saved
    return mod


@pytest.mark.unit
class TestBusinessOpsPackStructure:
    def test_required_files_exist(self):
        required = [
            "pack.yaml",
            "cfg/runtime-config.yaml",
            "cfg/thread-routing-policy.yaml",
            "cfg/decision-precedent-policy.yaml",
            "cfg/domain-profile-extension.yaml",
            "cfg/domain-role-map.yaml",
            "profiles/entity.yaml",
            "prompts/domain-persona-v1.md",
            "controllers/runtime_adapters.py",
            "controllers/nlp_pre_interpreter.py",
            "domain-lib/reference/turn-interpretation-spec-v1.md",
            "domain-lib/reference/auto-repair-task-event-contract-v1.md",
            "domain-lib/reference/auto-repair-provider-portability-checklist-v1.md",
            "domain-lib/reference/single-box-deployment-topology-v1.md",
            "modules/auto-repair/module-config.yaml",
            "modules/auto-repair/domain-physics.yaml",
            "modules/auto-repair/domain-physics.json",
            "modules/auto-repair/tool-adapters/erp-draft-staging-adapter-v1.yaml",
        ]
        missing = [rel for rel in required if not (PACK / rel).is_file()]
        assert not missing

    def test_pack_identity(self):
        data = _load_yaml(PACK / "pack.yaml")
        assert data["pack_id"] == "business-ops"
        assert data["default_module"] == "auto-repair"
        assert "auto-repair" in data["modules"]

    def test_runtime_config_has_required_runtime_paths(self):
        data = _load_yaml(PACK / "cfg" / "runtime-config.yaml")
        runtime = data["runtime"]
        required = [
            "domain_system_prompt_path",
            "turn_interpretation_prompt_path",
            "domain_physics_path",
            "subject_profile_path",
        ]
        for key in required:
            assert key in runtime
            assert isinstance(runtime[key], str)
            assert (REPO_ROOT / runtime[key]).exists()

    def test_runtime_config_preserves_policy_pointers(self):
        data = _load_yaml(PACK / "cfg" / "runtime-config.yaml")
        assert data["thread_routing_policy_path"] == "model-packs/business-ops/cfg/thread-routing-policy.yaml"
        assert data["decision_precedent_policy_path"] == "model-packs/business-ops/cfg/decision-precedent-policy.yaml"

    def test_role_map_contains_expected_business_roles(self):
        role_map = _load_yaml(PACK / "cfg" / "domain-role-map.yaml")
        roles = set((role_map.get("roles") or {}).keys())
        assert {"owner", "manager", "operator", "front_desk", "customer_intake"}.issubset(roles)

    def test_domain_physics_has_core_sections(self):
        physics = json.loads((PACK / "modules" / "auto-repair" / "domain-physics.json").read_text(encoding="utf-8"))
        for key in ("id", "version", "admin", "meta_authority_id", "invariants", "standing_orders", "escalation_triggers", "artifacts"):
            assert key in physics
        assert physics["id"] == "domain/bizops/auto-repair/v1"
        assert physics["artifacts"] == []

    def test_auto_repair_contract_references_live_in_subsystem_configs(self):
        physics = json.loads((PACK / "modules" / "auto-repair" / "domain-physics.json").read_text(encoding="utf-8"))
        refs = (((physics.get("subsystem_configs") or {}).get("contract_references") or {}).get("references") or [])

        assert len(refs) == 4
        by_id = {entry["id"]: entry for entry in refs}
        assert set(by_id.keys()) == {
            "service_intake_packet",
            "estimate_context_packet",
            "customer_communication_draft_packet",
            "provider_portability_checklist",
        }
        assert by_id["service_intake_packet"]["path"].endswith("auto-repair-task-event-contract-v1.md")
        assert by_id["provider_portability_checklist"]["path"].endswith("auto-repair-provider-portability-checklist-v1.md")
        assert all(entry["type"] == "contract_reference" for entry in refs)

    def test_auto_repair_module_config_exposes_auditable_thresholds(self):
        module_cfg = _load_yaml(PACK / "modules" / "auto-repair" / "module-config.yaml")
        confidence = module_cfg["confidence_profile_defaults"]
        escalation = module_cfg["escalation_profile_defaults"]
        allowlist = module_cfg["connector_allowlist_defaults"]

        assert 0 < float(confidence["confirmation_threshold"]) < float(confidence["suggest_threshold"]) <= 1
        assert int(confidence["stale_after_days"]) > 0
        assert float(confidence["stale_penalty"]) >= 0
        assert float(confidence["missing_precedent_penalty"]) >= 0

        assert int(escalation["manager_review_sla_minutes"]) > 0
        assert int(escalation["cto_review_sla_minutes"]) >= int(escalation["manager_review_sla_minutes"])
        assert isinstance(escalation["irreversible_actions_require_human_approval"], bool)

        assert "service/work-order" in allowlist["capabilities"]
        assert "query" in allowlist["action_classes"]
        assert "request_commit" in allowlist["action_classes"]

    def test_auto_repair_contract_docs_define_vertical_packets(self):
        contract_text = (PACK / "domain-lib" / "reference" / "auto-repair-task-event-contract-v1.md").read_text(encoding="utf-8")
        portability_text = (PACK / "domain-lib" / "reference" / "auto-repair-provider-portability-checklist-v1.md").read_text(encoding="utf-8")

        assert "service_intake_packet" in contract_text
        assert "estimate_context_packet" in contract_text
        assert "customer_communication_draft_packet" in contract_text
        assert "confidence_and_escalation_profile_defaults" in contract_text
        assert "## checklist" in portability_text


@pytest.mark.unit
class TestBusinessOpsAdapters:
    @pytest.fixture(autouse=True)
    def _load_module(self):
        self.mod = _import_module_from_path(
            "business_ops_runtime_adapters",
            PACK / "controllers" / "runtime_adapters.py",
        )

    def test_build_initial_state_has_expected_keys(self):
        state = self.mod.build_initial_state({"entity_state": {"open_draft_count": 2}})
        assert state["open_draft_count"] == 2
        assert state["turn_count"] == 0

    def test_domain_step_escalates_high_risk_without_approval(self):
        _, decision = self.mod.domain_step({}, {}, {"contains_high_risk_terms": True, "explicit_approval_language": False}, {})
        assert decision["tier"] == "major"
        assert decision["action"] == "escalate"

    def test_domain_step_stages_draft_when_approved(self):
        state, decision = self.mod.domain_step({}, {}, {"contains_high_risk_terms": False, "explicit_approval_language": True}, {})
        assert decision["action"] == "stage_erp_draft_update"
        assert state["open_draft_count"] == 1

    def test_domain_step_emits_canonical_query_for_service_intake_packet(self):
        state, decision = self.mod.domain_step(
            {},
            {},
            {"workflow_packet_type": "service_intake_packet", "confidence_score": 0.92},
            {
                "connector_allowlist_defaults": {
                    "capabilities": ["service/work-order"],
                    "action_classes": ["query", "update_draft", "request_commit"],
                }
            },
        )

        assert decision["action"] == "recommend_next_step"
        assert decision["capability_namespace"] == "service/work-order"
        assert decision["action_class"] == "query"
        assert decision["workflow_packet_type"] == "service_intake_packet"
        assert state["workflow_packet_type"] == "estimate_context_packet"

    def test_domain_step_requires_approval_before_customer_draft_stage(self):
        state, decision = self.mod.domain_step(
            {"workflow_packet_type": "customer_communication_draft_packet"},
            {},
            {"explicit_approval_language": False},
            {
                "connector_allowlist_defaults": {
                    "capabilities": ["service/work-order"],
                    "action_classes": ["query", "update_draft", "request_commit"],
                }
            },
        )

        assert decision["action"] == "recommend_next_step"
        assert decision["action_class"] == "query"
        assert decision["tier"] == "major"
        assert state["open_draft_count"] == 0

    def test_domain_step_customer_draft_with_approval_uses_update_draft(self):
        state, decision = self.mod.domain_step(
            {"workflow_packet_type": "customer_communication_draft_packet"},
            {},
            {"explicit_approval_language": True},
            {
                "connector_allowlist_defaults": {
                    "capabilities": ["service/work-order"],
                    "action_classes": ["query", "update_draft", "request_commit"],
                }
            },
        )

        assert decision["action"] == "stage_erp_draft_update"
        assert decision["action_class"] == "update_draft"
        assert state["open_draft_count"] == 1

    def test_domain_step_escalates_on_allowlist_violation(self):
        state, decision = self.mod.domain_step(
            {},
            {},
            {"workflow_packet_type": "service_intake_packet"},
            {
                "connector_allowlist_defaults": {
                    "capabilities": ["inventory"],
                    "action_classes": ["update_draft"],
                }
            },
        )

        assert decision["action"] == "escalate"
        assert decision["capability_namespace"] is None
        assert decision["action_class"] is None
        assert state["workflow_packet_type"] == "service_intake_packet"


@pytest.mark.unit
class TestBusinessOpsRolePermissions:
    def test_role_map_aligns_with_runtime_domain_roles(self):
        runtime_roles = set((_load_yaml(PACK / "cfg" / "runtime-config.yaml")["runtime"].get("domain_roles") or {}).keys())
        mapped_roles = set((_load_yaml(PACK / "cfg" / "domain-role-map.yaml").get("roles") or {}).keys())
        assert runtime_roles == mapped_roles

    def test_manager_write_allowed_operator_write_blocked(self):
        module_permissions = {
            "mode": "750",
            "owner": "owner-1",
            "group": "ops_staff",
            "acl": [],
        }
        groups_config = {
            "ops_staff": {
                "members": {
                    "domain_roles": ["owner", "manager", "operator", "front_desk"],
                }
            }
        }
        domain_roles_config = {
            "roles": [
                {"role_id": "owner", "default_access": "rwx", "hierarchy_level": 1},
                {"role_id": "manager", "default_access": "rwx", "hierarchy_level": 2},
                {"role_id": "operator", "default_access": "rx", "hierarchy_level": 3},
                {"role_id": "front_desk", "default_access": "r", "hierarchy_level": 4},
                {"role_id": "customer_intake", "default_access": "r", "hierarchy_level": 5},
            ],
        }

        assert check_permission(
            user_id="u-manager",
            user_role="user",
            module_permissions=module_permissions,
            operation=Operation.WRITE,
            domain_role="manager",
            domain_roles_config=domain_roles_config,
            groups_config=groups_config,
        )
        assert not check_permission(
            user_id="u-operator",
            user_role="user",
            module_permissions=module_permissions,
            operation=Operation.WRITE,
            domain_role="operator",
            domain_roles_config=domain_roles_config,
            groups_config=groups_config,
        )

    def test_min_tier_enforces_user_floor(self):
        assert check_min_tier("user", "user")
        assert check_min_tier("operator", "user")
        assert not check_min_tier("guest", "user")


@pytest.mark.unit
class TestBusinessOpsProfileComposition:
    def test_profile_layers_merge_base_domain_role(self):
        base_profile = REPO_ROOT / "model-packs" / "system" / "cfg" / "base-entity-profile.yaml"
        domain_extension = PACK / "cfg" / "domain-profile-extension.yaml"
        role_profile = PACK / "profiles" / "entity.yaml"

        profile = _assemble_profile(
            str(base_profile),
            str(domain_extension),
            str(role_profile),
        )

        assert profile["consent"]["accepted"] is False
        assert profile["organization_context"]["timezone"] == "UTC"
        assert profile["external_refs"]["erp_system"] == "erpnext"
        assert profile["preferences"]["explanation_style"] == "concise"
        assert profile["entity_state"]["open_draft_count"] == 0

    def test_role_profile_overrides_domain_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base.yaml"
            domain_path = Path(temp_dir) / "domain.yaml"
            role_path = Path(temp_dir) / "role.yaml"

            base_path.write_text("preferences:\n  explanation_style: long\n", encoding="utf-8")
            domain_path.write_text("preferences:\n  explanation_style: medium\n", encoding="utf-8")
            role_path.write_text("preferences:\n  explanation_style: concise\n", encoding="utf-8")

            merged = _assemble_profile(str(base_path), str(domain_path), str(role_path))
            assert merged["preferences"]["explanation_style"] == "concise"
