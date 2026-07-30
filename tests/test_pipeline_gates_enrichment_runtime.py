"""Targeted unit tests for uncovered pipeline helper branches.

These tests avoid server startup and exercise pure helper functions in:
- lumina.api.pipeline.gates
- lumina.api.pipeline.enrichment
- lumina.api.runtime_helpers (interpret_turn_input)
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

import lumina.api.runtime_helpers as rh
from lumina.api.pipeline.enrichment import enrich_turn_data, pre_enrich_rag
from lumina.api.pipeline.gates import (
    check_consent_gate,
    check_session_freeze,
    check_user_freeze,
)
from lumina.api.pipeline.response import build_escalation_content


class _Hit:
    def __init__(self, text: str, source: str, heading: str, score: float) -> None:
        self.chunk = SimpleNamespace(text=text, source_path=source, heading=heading)
        self.score = score


@pytest.mark.unit
def test_check_user_freeze_no_user_returns_none() -> None:
    result = check_user_freeze("s1", "hello", None, "system", {"domain_id": "system"}, {})
    assert result is None


@pytest.mark.unit
def test_check_user_freeze_not_frozen_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lumina.core.session_unlock.is_user_frozen", lambda _uid: False)
    result = check_user_freeze("s1", "hello", {"sub": "u1"}, "system", {"domain_id": "system"}, {})
    assert result is None


@pytest.mark.unit
def test_check_user_freeze_invalid_pin_returns_frozen_card(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lumina.core.session_unlock.is_user_frozen", lambda _uid: True)
    result = check_user_freeze("s1", "not-a-pin", {"sub": "u1"}, "system", {"domain_id": "system"}, {})
    assert result is not None
    assert result["action"] == "user_frozen"
    assert result["escalated"] is True


@pytest.mark.unit
def test_check_user_freeze_valid_pin_unlocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lumina.core.session_unlock.is_user_frozen", lambda _uid: True)
    monkeypatch.setattr("lumina.core.session_unlock.validate_unlock_pin", lambda _sid, _pin: True)
    unfreeze_calls: list[str] = []
    monkeypatch.setattr("lumina.core.session_unlock.unfreeze_user", lambda uid: unfreeze_calls.append(uid))
    monkeypatch.setattr(
        "lumina.core.session_unlock._FROZEN_USERS",
        {"u1": {"session_id": "locked-sid"}},
    )

    locked_container = SimpleNamespace(frozen=True)
    result = check_user_freeze(
        "s1",
        "123456",
        {"sub": "u1"},
        "system",
        {"domain_id": "system"},
        {"locked-sid": locked_container},
    )
    assert result is None
    assert locked_container.frozen is False
    assert unfreeze_calls == ["u1"]


@pytest.mark.unit
def test_check_session_freeze_not_frozen_returns_none() -> None:
    container = SimpleNamespace(frozen=False)
    result = check_session_freeze(
        "s1",
        "hello",
        {"sub": "u1"},
        "system",
        {"domain_id": "system"},
        {"s1": container},
    )
    assert result is None


@pytest.mark.unit
def test_check_session_freeze_invalid_pin_returns_frozen_card(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lumina.core.session_unlock.validate_unlock_pin", lambda _sid, _pin: False)
    container = SimpleNamespace(frozen=True)
    result = check_session_freeze(
        "s1",
        "123456",
        {"sub": "u1"},
        "system",
        {"domain_id": "system"},
        {"s1": container},
    )
    assert result is not None
    assert result["action"] == "session_frozen"
    assert container.frozen is True


@pytest.mark.unit
def test_check_session_freeze_valid_pin_unlocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lumina.core.session_unlock.validate_unlock_pin", lambda _sid, _pin: True)
    unfreeze_calls: list[str] = []
    monkeypatch.setattr("lumina.core.session_unlock.unfreeze_user", lambda uid: unfreeze_calls.append(uid))
    container = SimpleNamespace(frozen=True)

    result = check_session_freeze(
        "s1",
        "123456",
        {"sub": "u1"},
        "system",
        {"domain_id": "system"},
        {"s1": container},
    )
    assert result is not None
    assert result["action"] == "session_unlocked"
    assert container.frozen is False
    assert unfreeze_calls == ["u1"]


@pytest.mark.unit
def test_check_consent_gate_governance_role_bypasses() -> None:
    container = SimpleNamespace(consent_accepted=False, consent_timestamp=None)
    result = check_consent_gate(
        "s1",
        {"sub": "admin-1", "role": "admin"},
        "system",
        {"domain_id": "system"},
        {"pre_turn_checks": [{"id": "consent_boundary", "enabled": True}]},
        {"s1": container},
        persistence=MagicMock(),
    )
    assert result is None


@pytest.mark.unit
def test_check_consent_gate_uses_persisted_acceptance() -> None:
    container = SimpleNamespace(consent_accepted=False, consent_timestamp=None)
    persistence = MagicMock()
    persistence.get_user_consent.return_value = {"accepted": True, "timestamp": 123.0}

    result = check_consent_gate(
        "s1",
        {"sub": "u1", "role": "user"},
        "business-ops",
        {"domain_id": "business-ops"},
        {"pre_turn_checks": [{"id": "consent_boundary", "enabled": True}]},
        {"s1": container},
        persistence=persistence,
    )
    assert result is None
    assert container.consent_accepted is True
    assert container.consent_timestamp == 123.0


@pytest.mark.unit
def test_check_consent_gate_blocks_when_required() -> None:
    container = SimpleNamespace(consent_accepted=False, consent_timestamp=None)
    persistence = MagicMock()
    persistence.get_user_consent.return_value = None

    result = check_consent_gate(
        "s1",
        {"sub": "u1", "role": "user"},
        "business-ops",
        {"domain_id": "business-ops"},
        {"pre_turn_checks": [{"id": "consent_boundary", "enabled": True}]},
        {"s1": container},
        persistence=persistence,
    )
    assert result is not None
    assert result["action"] == "consent_required"


@pytest.mark.unit
def test_check_consent_gate_already_accepted_container_bypasses() -> None:
    container = SimpleNamespace(consent_accepted=True, consent_timestamp=10.0)
    result = check_consent_gate(
        "s1",
        {"sub": "u1", "role": "user"},
        "business-ops",
        {"domain_id": "business-ops"},
        {"pre_turn_checks": [{"id": "consent_boundary", "enabled": True}]},
        {"s1": container},
        persistence=MagicMock(),
    )
    assert result is None


@pytest.mark.unit
def test_check_consent_gate_persistence_error_falls_through_to_block() -> None:
    container = SimpleNamespace(consent_accepted=False, consent_timestamp=None)
    persistence = MagicMock()
    persistence.get_user_consent.side_effect = RuntimeError("db unavailable")

    result = check_consent_gate(
        "s1",
        {"sub": "u1", "role": "user"},
        "business-ops",
        {"domain_id": "business-ops"},
        {"pre_turn_checks": [{"id": "consent_boundary", "enabled": True}]},
        {"s1": container},
        persistence=persistence,
    )
    assert result is not None
    assert result["action"] == "consent_required"


@pytest.mark.unit
def test_pre_enrich_rag_filters_to_module(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = [
        _Hit("a" * 20, "model-packs/business-ops/modules/auto-repair/doc.md", "h1", 0.91234),
        _Hit("b" * 20, "model-packs/system/domain-lib/reference.md", "h2", 0.8),
    ]
    monkeypatch.setattr("lumina.core.nlp.search_domain", lambda *_args, **_kwargs: hits)

    result = pre_enrich_rag("need help", "business-ops", module_key="auto-repair")
    assert len(result) == 2
    assert any(r["source"].endswith("auto-repair/doc.md") for r in result)
    assert any("/modules/" not in r["source"] for r in result)
    assert result[0]["score"] == 0.9123


@pytest.mark.unit
def test_pre_enrich_rag_exceptions_are_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("lumina.core.nlp.search_domain", _raise)
    assert pre_enrich_rag("need help", "business-ops") == []


@pytest.mark.unit
def test_enrich_turn_data_with_pre_rag_slm_and_latency() -> None:
    turn_data: dict[str, Any] = {"intent": "read"}
    slm_fn = MagicMock(return_value={"summary": "compact"})

    result = enrich_turn_data(
        turn_data=turn_data,
        input_text="list users",
        domain_physics={"id": "domain/bizops/auto-repair/v1"},
        glossary=[],
        resolved_domain_id="business-ops",
        actor_elapsed=1.25,
        deterministic_response=False,
        module_key="auto-repair",
        slm_available_fn=lambda: True,
        slm_interpret_physics_context_fn=slm_fn,
        rag_context=[{"text": "ctx", "source": "x", "heading": "h", "score": 0.9}],
    )
    assert result["_slm_context"] == {"summary": "compact"}
    assert result["_rag_context"][0]["text"] == "ctx"
    assert result["response_latency_sec"] == 1.25


@pytest.mark.unit
def test_enrich_turn_data_inline_rag_and_telemetry(monkeypatch: pytest.MonkeyPatch) -> None:
    hits = [_Hit("c" * 20, "model-packs/business-ops/modules/auto-repair/rules.md", "rules", 0.77)]
    monkeypatch.setattr("lumina.core.nlp.search_domain", lambda *_args, **_kwargs: hits)
    monkeypatch.setattr(
        "lumina.daemon.resource_monitor.get_status",
        lambda: {"enabled": True, "telemetry_window": [{"cpu": 0.3}]},
    )

    result = enrich_turn_data(
        turn_data={},
        input_text="show me options",
        domain_physics={},
        glossary=[],
        resolved_domain_id="business-ops",
        actor_elapsed=None,
        deterministic_response=True,
        module_key="auto-repair",
        slm_available_fn=lambda: False,
        slm_interpret_physics_context_fn=lambda **_kwargs: {},
        rag_context=None,
    )
    assert "_rag_context" in result
    assert result["_system_telemetry"] == [{"cpu": 0.3}]


@pytest.mark.unit
def test_enrich_turn_data_telemetry_failure_is_non_blocking(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("lumina.core.nlp.search_domain", lambda *_args, **_kwargs: [])

    def _telemetry_raise():
        raise RuntimeError("telemetry unavailable")

    monkeypatch.setattr("lumina.daemon.resource_monitor.get_status", _telemetry_raise)

    result = enrich_turn_data(
        turn_data={},
        input_text="hello",
        domain_physics={},
        glossary=[],
        resolved_domain_id="system",
        actor_elapsed=None,
        deterministic_response=True,
        module_key=None,
        slm_available_fn=lambda: False,
        slm_interpret_physics_context_fn=lambda **_kwargs: {},
        rag_context=None,
    )
    assert isinstance(result, dict)


@pytest.mark.unit
def test_enrich_turn_data_inline_rag_exception_is_non_blocking(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args, **_kwargs):
        raise RuntimeError("rag unavailable")

    monkeypatch.setattr("lumina.core.nlp.search_domain", _raise)
    monkeypatch.setattr("lumina.daemon.resource_monitor.get_status", lambda: {"enabled": False})

    result = enrich_turn_data(
        turn_data={"base": 1},
        input_text="hello",
        domain_physics={},
        glossary=[],
        resolved_domain_id="system",
        actor_elapsed=None,
        deterministic_response=True,
        module_key=None,
        slm_available_fn=lambda: False,
        slm_interpret_physics_context_fn=lambda **_kwargs: {},
        rag_context=None,
    )
    assert result == {"base": 1}


@pytest.mark.unit
def test_interpret_turn_input_uses_slm_partial_and_mud_args(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def _interpreter(**kwargs):
        calls.append(kwargs)
        return {"ok": True}

    monkeypatch.setattr(rh, "slm_available", lambda: True)
    monkeypatch.setattr(rh, "classify_task_weight", lambda *_args, **_kwargs: rh.TaskWeight.LOW)

    runtime = {
        "turn_interpreter_fn": _interpreter,
        "turn_interpretation_prompt": "prompt",
        "turn_input_defaults": {"query_type": "general"},
        "tool_fns": {},
        "nlp_pre_interpreter_fn": lambda *_args: {"intent_type": "read"},
    }
    result = rh.interpret_turn_input(
        input_text="list users",
        task_context={"current_task": {}},
        runtime=runtime,
        world_sim_theme={"label": "theme"},
        mud_world_state={"zone": "hub"},
        slm_weight_overrides={"turn_interpretation": "low"},
    )
    assert result["ok"] is True
    assert len(calls) == 1
    assert getattr(calls[0]["call_llm"], "func", None) is rh.call_slm


@pytest.mark.unit
def test_interpret_turn_input_slm_failure_falls_back_to_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    state = {"calls": 0}

    def _interpreter(**kwargs):
        state["calls"] += 1
        call_llm_fn = kwargs["call_llm"]
        if getattr(call_llm_fn, "func", None) is rh.call_slm:
            raise RuntimeError("slm failed")
        return {"path": "llm"}

    monkeypatch.setattr(rh, "slm_available", lambda: True)
    monkeypatch.setattr(rh, "classify_task_weight", lambda *_args, **_kwargs: rh.TaskWeight.LOW)

    runtime = {
        "turn_interpreter_fn": _interpreter,
        "turn_interpretation_prompt": "prompt",
        "turn_input_defaults": {},
        "tool_fns": {},
    }
    result = rh.interpret_turn_input(
        input_text="status",
        task_context={},
        runtime=runtime,
        slm_weight_overrides={"turn_interpretation": "low"},
    )
    assert result == {"path": "llm"}
    assert state["calls"] == 2


@pytest.mark.unit
def test_render_contract_response_mud_keyerror_falls_back_to_plain() -> None:
    runtime = {
        "deterministic_templates_mud": {"inference": "MUD says {missing_key}"},
        "deterministic_templates": {"inference": "Plain {task_id}"},
    }
    result = rh.render_contract_response(
        {"prompt_type": "inference", "task_id": "t7"},
        runtime,
        mud_world_state={"zone": "yard"},
    )
    assert result == "Plain t7"


@pytest.mark.unit
def test_render_contract_response_mud_includes_theme_label() -> None:
    runtime = {
        "deterministic_templates_mud": {"inference": "Zone {zone} / Theme {theme_label}"},
        "deterministic_templates": {"inference": "Plain {task_id}"},
    }
    result = rh.render_contract_response(
        {"prompt_type": "inference", "task_id": "t7"},
        runtime,
        mud_world_state={"zone": "bay"},
        world_sim_theme={"label": "Auto Repair"},
    )
    assert result == "Zone bay / Theme Auto Repair"


@pytest.mark.unit
def test_interpret_turn_input_without_optional_args(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _interpreter(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(rh, "slm_available", lambda: False)

    runtime = {
        "turn_interpreter_fn": _interpreter,
        "turn_interpretation_prompt": "prompt",
        "turn_input_defaults": {},
        "tool_fns": {"x": lambda p: p},
        "nlp_pre_interpreter_fn": lambda *_args: {},
    }
    result = rh.interpret_turn_input(
        input_text="hello",
        task_context={},
        runtime=runtime,
        world_sim_theme=None,
        mud_world_state={"zone": "ignored"},
        slm_weight_overrides=None,
    )
    assert result == {"ok": True}
    assert captured["call_llm"] is rh.call_llm
    assert "call_slm" not in captured
    assert "nlp_pre_interpreter_fn" not in captured
    assert "mud_world_state" not in captured


@pytest.mark.unit
def test_interpret_turn_input_passes_declared_optional_args(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _interpreter(
        *,
        call_llm,
        input_text,
        task_context,
        prompt_text,
        default_fields,
        tool_fns,
        call_slm,
        nlp_pre_interpreter_fn,
        mud_world_state,
    ):
        captured.update(
            {
                "call_llm": call_llm,
                "input_text": input_text,
                "task_context": task_context,
                "prompt_text": prompt_text,
                "default_fields": default_fields,
                "tool_fns": tool_fns,
                "call_slm": call_slm,
                "nlp_pre_interpreter_fn": nlp_pre_interpreter_fn,
                "mud_world_state": mud_world_state,
            }
        )
        return {"ok": True}

    monkeypatch.setattr(rh, "slm_available", lambda: False)

    runtime = {
        "turn_interpreter_fn": _interpreter,
        "turn_interpretation_prompt": "prompt",
        "turn_input_defaults": {"a": 1},
        "tool_fns": {"x": lambda p: p},
        "nlp_pre_interpreter_fn": lambda *_args: {"intent": "read"},
    }
    result = rh.interpret_turn_input(
        input_text="hello",
        task_context={"ctx": 1},
        runtime=runtime,
        mud_world_state={"zone": "dock"},
    )
    assert result == {"ok": True}
    assert captured["call_slm"] is rh.call_slm
    assert callable(captured["nlp_pre_interpreter_fn"])
    assert captured["mud_world_state"] == {"zone": "dock"}


@pytest.mark.unit
def test_interpret_turn_input_non_slm_exception_is_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    def _interpreter(**_kwargs):
        raise ValueError("bad input")

    monkeypatch.setattr(rh, "slm_available", lambda: False)

    runtime = {
        "turn_interpreter_fn": _interpreter,
        "turn_interpretation_prompt": "prompt",
        "turn_input_defaults": {},
        "tool_fns": {},
    }
    with pytest.raises(ValueError, match="bad input"):
        rh.interpret_turn_input(
            input_text="hello",
            task_context={},
            runtime=runtime,
            slm_weight_overrides={"turn_interpretation": "low"},
        )


@pytest.mark.unit
def test_apply_tool_call_policy_non_dict_payload_is_coerced_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rh, "render_template_value", lambda *_args, **_kwargs: "not-a-dict")
    runtime = {
        "tool_call_policies": {"inference": [{"tool_id": "checker", "payload": {"a": 1}}]},
        "tool_fns": {"checker": lambda payload: {"seen_payload": payload}},
    }
    out = rh.apply_tool_call_policy("inference", {}, {}, {}, runtime)
    assert out[0]["payload"] == {}
    assert out[0]["result"]["seen_payload"] == {}


@pytest.mark.unit
def test_build_escalation_content_no_escalation_record() -> None:
    orch = SimpleNamespace(log_records=[{"record_type": "TraceEvent", "session_id": "s1"}])
    escalated, content = build_escalation_content(
        session_id="s1",
        orchestrator=orch,
        resolved_domain_id="system",
        runtime={},
        active_mod={},
    )
    assert escalated is False
    assert content is None


@pytest.mark.unit
def test_build_escalation_content_with_runtime_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    orch = SimpleNamespace(log_records=[
        {"record_type": "TraceEvent", "session_id": "s1"},
        {"record_type": "EscalationRecord", "session_id": "s1", "reason": "risk"},
    ])

    monkeypatch.setattr(
        "lumina.api.structured_content.build_escalation_card",
        lambda rec, session_context: {"record": rec, "session_context": session_context},
    )

    def _esc_ctx_fn(**_kwargs):
        return {"domain_id": "system", "actor_pseudonym": "actor-001"}

    escalated, content = build_escalation_content(
        session_id="s1",
        orchestrator=orch,
        resolved_domain_id="system",
        runtime={"escalation_context_fn": _esc_ctx_fn},
        active_mod={},
    )
    assert escalated is True
    assert content is not None
    assert content["session_context"]["actor_pseudonym"] == "actor-001"


@pytest.mark.unit
def test_build_escalation_content_with_active_module_hook_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    orch = SimpleNamespace(log_records=[
        {"record_type": "EscalationRecord", "session_id": "s1", "reason": "policy"},
    ])

    monkeypatch.setattr(
        "lumina.api.structured_content.build_escalation_card",
        lambda rec, session_context: {"record": rec, "session_context": session_context},
    )

    def _runtime_ctx_fn(**_kwargs):
        return {"domain_id": "system", "actor_pseudonym": "runtime"}

    def _active_ctx_fn(**_kwargs):
        return {"domain_id": "system", "actor_pseudonym": "active"}

    escalated, content = build_escalation_content(
        session_id="s1",
        orchestrator=orch,
        resolved_domain_id="system",
        runtime={"escalation_context_fn": _runtime_ctx_fn},
        active_mod={"escalation_context_fn": _active_ctx_fn},
    )
    assert escalated is True
    assert content is not None
    assert content["session_context"]["actor_pseudonym"] == "active"


@pytest.mark.unit
def test_build_escalation_content_fallback_actor_from_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    writer = SimpleNamespace(_profile={"subject_id": "subject-xyz"})
    orch = SimpleNamespace(
        _writer=writer,
        log_records=[
            {"record_type": "EscalationRecord", "session_id": "s1", "reason": "policy"},
        ],
    )

    monkeypatch.setattr(
        "lumina.api.structured_content.build_escalation_card",
        lambda rec, session_context: {"record": rec, "session_context": session_context},
    )

    escalated, content = build_escalation_content(
        session_id="s1",
        orchestrator=orch,
        resolved_domain_id="business-ops",
        runtime={},
        active_mod={},
    )
    assert escalated is True
    assert content is not None
    assert content["session_context"]["domain_id"] == "business-ops"
    assert content["session_context"]["actor_pseudonym"] == "subject-xyz"


@pytest.mark.unit
def test_build_escalation_content_handles_empty_record_window_after_detect() -> None:
    class _FlakyRecords:
        def __init__(self) -> None:
            self.calls = 0

        def __getitem__(self, key):
            if not isinstance(key, slice):
                return []
            self.calls += 1
            if self.calls == 1:
                return [{"record_type": "EscalationRecord", "session_id": "s1"}]
            return []

    orch = SimpleNamespace(log_records=_FlakyRecords())
    escalated, content = build_escalation_content(
        session_id="s1",
        orchestrator=orch,
        resolved_domain_id="system",
        runtime={},
        active_mod={},
    )
    assert escalated is True
    assert content is None
