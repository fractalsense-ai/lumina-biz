from __future__ import annotations

import json
from typing import Any, Callable


def build_initial_state(profile: dict[str, Any]) -> dict[str, Any]:
    entity_state = profile.get("entity_state") or {}
    return {
        "open_draft_count": int(entity_state.get("open_draft_count", 0)),
        "last_recommendation_tier": entity_state.get("last_recommendation_tier"),
        "turn_count": 0,
    }


def domain_step(
    state: dict[str, Any],
    task_spec: dict[str, Any],
    evidence: dict[str, Any],
    params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    new_state = dict(state)
    new_state["turn_count"] = int(new_state.get("turn_count", 0)) + 1

    high_risk = bool(evidence.get("contains_high_risk_terms", False))
    approved = bool(evidence.get("explicit_approval_language", False))

    if high_risk and not approved:
        tier = "major"
        action = "escalate"
    elif approved:
        tier = "minor"
        action = "stage_erp_draft_update"
        new_state["open_draft_count"] = int(new_state.get("open_draft_count", 0)) + 1
    else:
        tier = "ok"
        action = "recommend_next_step"

    new_state["last_recommendation_tier"] = tier
    return new_state, {
        "tier": tier,
        "action": action,
        "escalation_eligible": high_risk,
    }


def _strip_markdown_fences(raw: str) -> str:
    cleaned = (raw or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[: cleaned.rfind("```")]
    return cleaned.strip()


def interpret_turn_input(
    call_llm: Callable[[str, str, str | None], str],
    input_text: str,
    task_context: dict[str, Any],
    prompt_text: str,
    default_fields: dict[str, Any] | None = None,
    tool_fns: dict[str, Callable[..., Any]] | None = None,
) -> dict[str, Any]:
    raw_response = call_llm(system=prompt_text, user=f"Operator message: {input_text}", model=None)

    try:
        evidence = json.loads(_strip_markdown_fences(raw_response))
    except (json.JSONDecodeError, IndexError):
        evidence = {}

    defaults = dict(default_fields or {})
    if not defaults:
        defaults = {
            "risk_class": "operational",
            "contains_high_risk_terms": False,
            "explicit_approval_language": False,
        }

    for key, default_value in defaults.items():
        if key not in evidence or evidence[key] is None:
            evidence[key] = default_value

    return evidence
