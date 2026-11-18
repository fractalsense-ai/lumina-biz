"""Unit tests for Slice 40 N3 pipeline-order enforcement.

These tests are intentionally domain-neutral and validate only
runtime stage-order behavior in ``process_message``.
"""
from __future__ import annotations

from contextlib import ExitStack
import json
import logging
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


def _make_runtime() -> dict[str, Any]:
    return {
        "system_prompt": "sys",
        "domain": {"id": "system", "version": "1", "glossary": []},
        "runtime_provenance": {},
        "turn_input_schema": {},
        "turn_input_defaults": {"query_type": "general", "urgency": "routine"},
        "turn_interpretation_prompt": "interpret",
        "slm_weight_overrides": {},
        "tool_fns": None,
        "action_prompt_type_map": {},
        "deterministic_templates": {},
        "local_only": False,
    }


def _make_session(task_presented_at: float) -> dict[str, Any]:
    orch = MagicMock()
    orch.state = SimpleNamespace()
    orch.log_records = []
    orch.get_standing_order_attempts.return_value = {}
    orch.append_provenance_trace.return_value = None
    orch.process_turn.return_value = (
        {
            "prompt_type": "task_presentation",
            "model_pack_id": "system",
            "model_pack_version": "1",
            "task_id": "t1",
            "task_nominal_difficulty": 0.3,
            "skills_targeted": [],
            "theme": None,
            "standing_order_trigger": None,
            "references": [],
            "grounded": True,
        },
        "task_presentation",
    )
    return {
        "orchestrator": orch,
        "task_spec": {"task_id": "t1", "nominal_difficulty": 0.3, "skills_required": []},
        "current_task": {"task_id": "t1"},
        "turn_count": 0,
        "domain_id": "system",
        "task_presented_at": task_presented_at,
    }


def _common_patches(proc, *, session: dict[str, Any], runtime: dict[str, Any]):
    return (
        patch.object(proc, "get_or_create_session", return_value=session),
        patch.object(proc._cfg.DOMAIN_REGISTRY, "get_runtime_context", return_value=runtime),
        patch.object(proc, "check_user_freeze", return_value=None),
        patch.object(proc, "check_session_freeze", return_value=None),
        patch.object(proc, "check_consent_gate", return_value=None),
        patch.object(proc, "check_glossary", return_value=None),
        patch.object(proc, "check_turn_0", return_value=None),
        patch.object(proc, "resolve_greeting_eligible", return_value=False),
        patch.object(proc, "check_greeting", return_value=None),
        patch.object(proc, "slm_available", return_value=False),
        patch.object(proc, "normalize_turn_data", side_effect=lambda d, _s: d),
        patch.object(proc, "apply_tool_call_policy", return_value=[]),
        patch.object(proc, "strip_latex_delimiters", side_effect=lambda s: s),
        patch.object(proc, "_invoke_llm", return_value="ok"),
        patch("lumina.api.processing._session_containers", {}),
        patch("lumina.api.processing._persist_session_container"),
    )


@pytest.mark.unit
def test_pipeline_order_guard_rejects_reordered_stages() -> None:
    from lumina.api.processing import _pipeline_order_violation

    assert _pipeline_order_violation(
        ["nlp", "auth"],
        [],
        next_stage="semantic_routing",
    ) == "pipeline_stage_order_invalid"
    assert _pipeline_order_violation(
        ["auth", "nlp", "ppa"],
        [],
        next_stage="semantic_routing",
    ) == "pipeline_stage_order_invalid"


@pytest.mark.unit
def test_pipeline_order_guard_allows_nlp_bypass_only_with_degraded_reason() -> None:
    from lumina.api.processing import _pipeline_order_violation

    assert _pipeline_order_violation(
        ["auth"],
        ["nlp_stage_bypassed_deterministic"],
        next_stage="semantic_routing",
    ) is None
    assert _pipeline_order_violation(
        ["auth"],
        [],
        next_stage="semantic_routing",
    ) == "missing_nlp_stage"


@pytest.mark.unit
def test_pipeline_order_violation_denies_before_semantic_interpretation() -> None:
    from lumina.api import processing as proc

    session = _make_session(task_presented_at=time.time() - 1)
    runtime = _make_runtime()
    interpreter = MagicMock(return_value={"query_type": "general"})

    with ExitStack() as stack:
        for patcher in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(patcher)
        stack.enter_context(patch.object(proc, "interpret_turn_input", interpreter))
        stack.enter_context(
            patch.object(proc, "_pipeline_order_violation", return_value="pipeline_stage_order_invalid")
        )
        result = proc.process_message("sess-order-invalid", "hello", deterministic_response=False)

    assert result["action"] == "pipeline_order_denied"
    assert result["_pipeline_order"]["denied_reason"] == "pipeline_stage_order_invalid"
    interpreter.assert_not_called()
    session["orchestrator"].process_turn.assert_not_called()


@pytest.mark.unit
def test_glossary_intercept_runs_after_nlp_and_records_ppa_bypass(caplog) -> None:
    from lumina.api import processing as proc

    caplog.set_level(logging.INFO, logger="lumina-api")
    session = _make_session(task_presented_at=time.time() - 1)
    events: list[str] = []
    runtime = _make_runtime()
    runtime["nlp_pre_interpreter_fn"] = lambda _text, _ctx: events.append("nlp") or {}

    def _glossary_intercept(*_args, **_kwargs):
        events.append("glossary")
        return {
            "response": "definition",
            "action": "definition_lookup",
            "prompt_type": "definition_lookup",
            "escalated": False,
            "tool_results": None,
            "domain_id": "system",
        }

    with ExitStack() as stack:
        for patcher in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(patcher)
        stack.enter_context(patch.object(proc, "check_glossary", side_effect=_glossary_intercept))
        result = proc.process_message("sess-order-glossary", "define term", deterministic_response=False)

    assert events == ["nlp", "glossary"]
    assert result["_pipeline_order"]["stage_trace"] == ["auth", "nlp", "semantic_routing"]
    assert "ppa_bypassed_glossary_intercept" in result["_pipeline_order"]["degraded_reasons"]
    observations = [
        json.loads(record.getMessage().split("pipeline_order_observation ", 1)[1])
        for record in caplog.records
        if record.name == "lumina-api" and record.getMessage().startswith("pipeline_order_observation ")
    ]
    assert observations[-1]["degraded_reasons"] == ["ppa_bypassed_glossary_intercept"]
    assert observations[-1]["session_ref"]


@pytest.mark.unit
def test_pipeline_order_trace_includes_nlp_and_ppa() -> None:
    from lumina.api import processing as proc

    session = _make_session(task_presented_at=time.time() - 1)
    runtime = _make_runtime()
    runtime["nlp_pre_interpreter_fn"] = lambda _text, _ctx: {"intent_scores": {"alpha": 1}}

    with ExitStack() as stack:
        for p in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(p)
        stack.enter_context(patch.object(proc, "interpret_turn_input", return_value={"query_type": "general"}))
        result = proc.process_message("sess-order", "hello", deterministic_response=False)

    pipeline_meta = result.get("_pipeline_order")
    assert isinstance(pipeline_meta, dict)
    assert pipeline_meta.get("contract") == "pipeline_order_enforcement_v1"
    assert pipeline_meta.get("stage_trace") == ["auth", "nlp", "semantic_routing", "ppa"]
    assert pipeline_meta.get("degraded") is False


@pytest.mark.unit
def test_pipeline_order_marks_degraded_when_nlp_bypassed_deterministic() -> None:
    from lumina.api import processing as proc

    session = _make_session(task_presented_at=time.time() - 1)
    runtime = _make_runtime()

    with ExitStack() as stack:
        for p in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(p)
        result = proc.process_message("sess-order-det", "hello", deterministic_response=True)

    pipeline_meta = result.get("_pipeline_order")
    assert isinstance(pipeline_meta, dict)
    assert pipeline_meta.get("degraded") is True
    reasons = pipeline_meta.get("degraded_reasons") or []
    assert "nlp_stage_bypassed_deterministic" in reasons
    assert "nlp_stage_not_executed" in reasons


@pytest.mark.unit
def test_pipeline_order_denies_when_semantic_output_invalid() -> None:
    from lumina.api import processing as proc

    session = _make_session(task_presented_at=time.time() - 1)
    runtime = _make_runtime()

    with ExitStack() as stack:
        for p in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(p)
        stack.enter_context(patch.object(proc, "interpret_turn_input", return_value=None))
        result = proc.process_message("sess-order-deny", "hello", deterministic_response=False)

    assert result["action"] == "pipeline_order_denied"
    assert result["escalated"] is True
    assert result["_pipeline_order"]["denied_reason"] == "semantic_routing_output_invalid"
    session["orchestrator"].process_turn.assert_not_called()
