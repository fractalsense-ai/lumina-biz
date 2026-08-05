from __future__ import annotations

import pytest

from lumina.core.policy_validation import validate_policy_header
from lumina.orchestrator.contract_drafter import ContractDrafter


@pytest.mark.unit
def test_validate_policy_header_accepts_supported_shape() -> None:
    cfg = {
        "schema_version": "1.0.0",
        "policy_version": "2026.08",
        "defaults": {},
        "organizations": {},
    }
    assert validate_policy_header(cfg, policy_name="access") == cfg


@pytest.mark.unit
def test_validate_policy_header_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError, match="unknown top-level fields"):
        validate_policy_header(
            {
                "schema_version": "1.0.0",
                "policy_version": "2026.08",
                "defaults": {},
                "organizations": {},
                "extra": True,
            },
            policy_name="access",
        )


@pytest.mark.unit
def test_validate_policy_header_rejects_unsupported_schema_version() -> None:
    with pytest.raises(ValueError, match="unsupported access policy schema_version"):
        validate_policy_header(
            {
                "schema_version": "2.0.0",
                "policy_version": "2026.08",
                "defaults": {},
                "organizations": {},
            },
            policy_name="access",
        )


@pytest.mark.unit
def test_contract_drafter_defaults_and_hint_mapping() -> None:
    drafter = ContractDrafter(
        domain_physics={"id": "pack/business-ops", "version": "1.2.3"},
        subject_profile={"preferences": {"interests": ["inventory"]}},
        action_prompt_type_map={"assist": "hint"},
    )

    contract = drafter.build(
        task_spec={"task_id": "t-1", "skills_required": ["analysis"]},
        action="assist",
        domain_lib_decision={"challenge": 0.4},
        standing_order_trigger="missing_info",
        references=[{"id": "r1"}],
    )

    assert contract["prompt_type"] == "hint"
    assert contract["hint_level"] == 1
    assert contract["theme"] == "inventory"
    assert contract["grounded"] is True
    assert contract["task_nominal_difficulty"] == 0.4


@pytest.mark.unit
def test_contract_drafter_unknown_action_passes_through_and_defaults() -> None:
    drafter = ContractDrafter(
        domain_physics={"id": "pack/business-ops", "version": "1.2.3"},
        subject_profile={"preferences": {}},
    )

    contract = drafter.build(
        task_spec={"task_id": "t-2", "nominal_difficulty": 0.9},
        action="custom_extension_action",
        domain_lib_decision={"challenge": 0.1},
        standing_order_trigger=None,
    )

    assert contract["prompt_type"] == "custom_extension_action"
    assert contract["task_nominal_difficulty"] == 0.9
    assert contract["theme"] is None
    assert contract["references"] == []
    assert contract["grounded"] is False