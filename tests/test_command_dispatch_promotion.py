"""Tests for command-dispatch promotion and deterministic fallback behavior.

Covers:
- _maybe_promote_query_type for command-discovery phrases.
- _deterministic_command_fallback for read and mutation intents.
- interpret_turn_input command dispatch behavior when SLM is unavailable.
- business-ops pre-interpreter high-risk and approval signal extraction.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_sys_mod = _load_module(
    _REPO_ROOT / "model-packs" / "system" / "controllers" / "runtime_adapters.py",
    "sys_runtime_adapters_test",
)

_biz_nlp_mod = _load_module(
    _REPO_ROOT / "model-packs" / "business-ops" / "controllers" / "nlp_pre_interpreter.py",
    "bizops_nlp_pre_interpreter_test",
)

_sys_maybe_promote = _sys_mod._maybe_promote_query_type
_sys_fallback = _sys_mod._deterministic_command_fallback
_sys_interpret_turn = _sys_mod.interpret_turn_input
_biz_pre_interpret = _biz_nlp_mod.pre_interpret


@pytest.mark.unit
class TestSystemQueryTypePromotion:
    def _promote(self, evidence: dict[str, Any], input_text: str) -> dict[str, Any]:
        _sys_maybe_promote(evidence, input_text)
        return evidence

    def test_promotes_command_discovery(self) -> None:
        ev = {"query_type": "general"}
        self._promote(ev, "what commands do I have available?")
        assert ev["query_type"] == "admin_command"

    def test_promotes_user_listing_phrase(self) -> None:
        ev = {"query_type": "general"}
        self._promote(ev, "show me all users")
        assert ev["query_type"] == "admin_command"

    def test_promotes_module_listing_phrase(self) -> None:
        ev = {"query_type": "general"}
        self._promote(ev, "list modules")
        assert ev["query_type"] == "admin_command"

    def test_does_not_promote_unrelated_text(self) -> None:
        ev = {"query_type": "general"}
        self._promote(ev, "hello there")
        assert ev["query_type"] == "general"

    def test_does_not_override_non_general(self) -> None:
        ev = {"query_type": "status_query"}
        self._promote(ev, "show me all users")
        assert ev["query_type"] == "status_query"


@pytest.mark.unit
class TestDeterministicFallback:
    def test_read_users_routes_to_list_users(self) -> None:
        result = _sys_fallback("list users", {"intent_type": "read"})
        assert result is not None
        assert result["operation"] == "list_users"
        assert result["params"] == {}

    def test_read_modules_routes_to_list_modules(self) -> None:
        result = _sys_fallback("show modules", {"intent_type": "read"})
        assert result is not None
        assert result["operation"] == "list_modules"

    def test_read_domains_routes_to_list_domains(self) -> None:
        result = _sys_fallback("list domains", {"intent_type": "read"})
        assert result is not None
        assert result["operation"] == "list_domains"

    def test_mutation_invite_user(self) -> None:
        result = _sys_fallback(
            "invite user alice",
            {
                "intent_type": "mutation",
                "_nlp_verb": "invite",
                "target_user": "alice",
                "target_role": "user",
            },
        )
        assert result is not None
        assert result["operation"] == "invite_user"
        assert result["params"]["username"] == "alice"


@pytest.mark.unit
class TestInterpretTurnInputDispatch:
    def _llm_response(self, query_type: str = "general") -> str:
        return json.dumps(
            {
                "query_type": query_type,
                "target_component": None,
                "urgency": "routine",
                "response_latency_sec": 5.0,
                "off_task_ratio": 0.0,
            }
        )

    def test_promotes_general_and_uses_fallback_dispatch(self) -> None:
        call_slm = MagicMock(return_value=self._llm_response("general"))

        mock_slm_mod = MagicMock()
        mock_slm_mod.slm_available = MagicMock(return_value=False)
        mock_slm_mod.slm_parse_admin_command = MagicMock(return_value=None)

        def _nlp_stub(_text: str, _ctx: dict[str, Any]) -> dict[str, Any]:
            return {
                "intent_type": "read",
                "_nlp_anchors": [],
            }

        with __import__("unittest.mock", fromlist=["patch"]).patch.dict(
            sys.modules, {"lumina.core.slm": mock_slm_mod}
        ):
            evidence = _sys_interpret_turn(
                call_llm=call_slm,
                input_text="what commands do I have available?",
                task_context={},
                prompt_text="You are a governance classifier.",
                call_slm=call_slm,
                nlp_pre_interpreter_fn=_nlp_stub,
            )

        assert evidence["query_type"] == "admin_command"
        assert evidence["command_dispatch"] is not None
        assert evidence["command_dispatch"]["operation"] == "list_commands"

    def test_preserves_admin_command_query_type(self) -> None:
        call_slm = MagicMock(return_value=self._llm_response("admin_command"))

        mock_slm_mod = MagicMock()
        mock_slm_mod.slm_available = MagicMock(return_value=False)
        mock_slm_mod.slm_parse_admin_command = MagicMock(return_value=None)

        with __import__("unittest.mock", fromlist=["patch"]).patch.dict(
            sys.modules, {"lumina.core.slm": mock_slm_mod}
        ):
            evidence = _sys_interpret_turn(
                call_llm=call_slm,
                input_text="list users",
                task_context={},
                prompt_text="You are a governance classifier.",
                call_slm=call_slm,
                nlp_pre_interpreter_fn=lambda *_: {"intent_type": "read", "_nlp_anchors": []},
            )

        assert evidence["query_type"] == "admin_command"
        assert evidence["command_dispatch"] is not None
        assert evidence["command_dispatch"]["operation"] == "list_users"


@pytest.mark.unit
class TestBusinessOpsPreInterpreter:
    def test_detects_high_risk_terms(self) -> None:
        result = _biz_pre_interpret("Customer reported injury risk and liability issue", {})
        assert result["contains_high_risk_terms"] is True

    def test_detects_explicit_approval_language(self) -> None:
        result = _biz_pre_interpret("Approved and confirmed, go ahead", {})
        assert result["explicit_approval_language"] is True

    def test_no_signals_for_neutral_text(self) -> None:
        result = _biz_pre_interpret("Need standard tire rotation update", {})
        assert result["contains_high_risk_terms"] is False
        assert result["explicit_approval_language"] is False
