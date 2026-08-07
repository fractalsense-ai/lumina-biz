"""Timing and payload regression tests for process_message.

These tests cover active contracts in src/lumina/api/processing.py:
- response_latency_sec is sampled at request arrival (before interpretation/LLM work)
- post_turn_timer_fn runs after LLM invocation
- llm payload receives answered-task snapshot even when post-turn replaces current_task
"""

from __future__ import annotations

from contextlib import ExitStack
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest



def _make_runtime(*, post_turn_processor_fn=None, post_turn_timer_fn=None) -> dict[str, Any]:
    return {
        "system_prompt": "sys",
        "domain": {"id": "biz", "version": "1", "glossary": []},
        "runtime_provenance": {},
        "turn_input_schema": {},
        "turn_input_defaults": {"query_type": "general", "urgency": "routine"},
        "turn_interpretation_prompt": "interpret",
        "slm_weight_overrides": {},
        "tool_fns": None,
        "action_prompt_type_map": {},
        "deterministic_templates": {},
        "local_only": False,
        "post_turn_processor_fn": post_turn_processor_fn,
        "post_turn_timer_fn": post_turn_timer_fn,
    }



def _make_session(*, task_presented_at: float, current_task: dict[str, Any] | None = None) -> dict[str, Any]:
    orch = MagicMock()
    orch.state = SimpleNamespace(world_sim_theme={}, mud_world_state={})
    orch.log_records = []
    orch.get_standing_order_attempts.return_value = {}
    orch.append_provenance_trace.return_value = None
    orch.process_turn.return_value = (
        {
            "prompt_type": "task_presentation",
            "model_pack_id": "biz",
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
        "current_task": current_task or {"equation": "x+3=7", "expected_answer": "4"},
        "turn_count": 0,
        "domain_id": "business-ops",
        "task_presented_at": task_presented_at,
    }



def _common_patches(proc, *, session: dict[str, Any], runtime: dict[str, Any], llm_return: str = "ok"):
    mock_persistence = MagicMock()
    return (
        patch.object(proc, "get_or_create_session", return_value=session),
        patch.object(proc._cfg, "DOMAIN_REGISTRY", MagicMock(**{"get_runtime_context.return_value": runtime})),
        patch.object(proc._cfg, "PERSISTENCE", mock_persistence),
        patch.object(proc, "check_user_freeze", return_value=None),
        patch.object(proc, "check_session_freeze", return_value=None),
        patch.object(proc, "check_consent_gate", return_value=None),
        patch.object(proc, "check_glossary", return_value=None),
        patch.object(proc, "check_turn_0", return_value=None),
        patch.object(proc, "resolve_greeting_eligible", return_value=False),
        patch.object(proc, "check_greeting", return_value=None),
        patch.object(proc, "detect_glossary_query", return_value=None),
        patch.object(proc, "slm_available", return_value=False),
        patch.object(proc, "interpret_turn_input", return_value={"query_type": "general"}),
        patch.object(proc, "normalize_turn_data", side_effect=lambda d, _s: d),
        patch.object(proc, "apply_tool_call_policy", return_value=[]),
        patch.object(proc, "strip_latex_delimiters", side_effect=lambda s: s),
        patch.object(proc, "assemble_llm_payload", return_value={"payload": True}),
        patch.object(proc, "_invoke_llm", return_value=llm_return),
        patch("lumina.api.processing._session_containers", {}),
        patch("lumina.api.processing._persist_session_container"),
    )


@pytest.mark.unit
def test_response_latency_sampled_at_request_arrival() -> None:
    from lumina.api import processing as proc

    presented = 1_000_000.0
    arrived = presented + 12.0

    session = _make_session(task_presented_at=presented)
    runtime = _make_runtime()

    with ExitStack() as stack:
        for p in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(p)
        mock_time = stack.enter_context(patch("lumina.api.processing.time"))
        mock_time.time.return_value = arrived
        proc.process_message("sess-latency", "list users", deterministic_response=False)

    turn_data_passed = session["orchestrator"].process_turn.call_args[0][1]
    assert abs(turn_data_passed["response_latency_sec"] - 12.0) < 0.01


@pytest.mark.unit
def test_post_turn_timer_runs_after_llm() -> None:
    from lumina.api import processing as proc

    call_order: list[str] = []

    def _timer_hook(**kwargs):
        call_order.append("timer")

    session = _make_session(task_presented_at=time.time() - 2)
    runtime = _make_runtime(post_turn_timer_fn=_timer_hook)

    with ExitStack() as stack:
        for p in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(p)
        stack.enter_context(
            patch.object(proc, "_invoke_llm", side_effect=lambda *a, **k: call_order.append("llm") or "ok")
        )
        proc.process_message("sess-timer", "hello", deterministic_response=False)

    assert call_order == ["llm", "timer"]


@pytest.mark.unit
def test_answered_task_snapshot_preserved_when_post_turn_replaces_current_task() -> None:
    from lumina.api import processing as proc

    old_task = {"equation": "6x=90", "expected_answer": "15"}
    new_task = {"equation": "7x=98", "expected_answer": "14"}

    def _post_turn_processor(**kwargs):
        return {
            "resolved_action": kwargs["resolved_action"],
            "current_task": dict(new_task),
            "new_task_presented": True,
        }

    captured: dict[str, Any] = {}

    def _capture_payload(prompt_contract, input_text, answered_task, current_task, new_task_presented, turn_data, tool_results, session_id, session_containers):
        captured["answered_task"] = answered_task
        captured["current_task"] = current_task
        captured["new_task_presented"] = new_task_presented
        return {"payload": True}

    session = _make_session(task_presented_at=time.time() - 3, current_task=dict(old_task))
    runtime = _make_runtime(post_turn_processor_fn=_post_turn_processor)

    with ExitStack() as stack:
        for p in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(p)
        stack.enter_context(patch.object(proc, "assemble_llm_payload", side_effect=_capture_payload))
        proc.process_message("sess-payload", "x=15", deterministic_response=False)

    assert captured["answered_task"] == old_task
    assert captured["current_task"] == new_task
    assert captured["new_task_presented"] is True


@pytest.mark.unit
def test_timer_hook_receives_context_fields() -> None:
    from lumina.api import processing as proc

    captured: dict[str, Any] = {}

    def _timer_hook(**kwargs):
        captured.update(kwargs)

    session = _make_session(task_presented_at=time.time() - 1)
    runtime = _make_runtime(post_turn_timer_fn=_timer_hook)

    with ExitStack() as stack:
        for p in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(p)
        proc.process_message("sess-hook", "status", deterministic_response=False)

    assert captured["session_id"] == "sess-hook"
    assert captured["resolved_action"] == "task_presentation"
    assert "session" in captured
    assert "session_containers" in captured


@pytest.mark.unit
def test_pipeline_order_trace_includes_nlp_and_ppa() -> None:
    from lumina.api import processing as proc

    session = _make_session(task_presented_at=time.time() - 1)
    runtime = _make_runtime()
    runtime["nlp_pre_interpreter_fn"] = lambda _text, _ctx: {"intent_scores": {"a": 1}}

    with ExitStack() as stack:
        for p in _common_patches(proc, session=session, runtime=runtime):
            stack.enter_context(p)
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
