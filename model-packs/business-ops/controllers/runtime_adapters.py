from __future__ import annotations

import json
from typing import Any, Callable


_PACKET_ORDER = (
    "service_intake_packet",
    "estimate_context_packet",
    "customer_communication_draft_packet",
    "escalation_record",
)

_ACTION_TO_HANDLER = {
    "recommend_next_step": "workflow.intake_or_status",
    "stage_erp_draft_update": "workflow.stage_draft_update",
    "escalate": "workflow.escalate_case",
}

_DEFAULT_ESCALATION_POLICY = {
    "major": {"target_role": "manager", "priority": "high", "sla_minutes": 15},
    "minor": {"target_role": "operator", "priority": "normal", "sla_minutes": 60},
    "ok": {"target_role": "operator", "priority": "normal", "sla_minutes": 240},
}


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _allowlisted(action: str, params: dict[str, Any]) -> bool:
    if "allowed_workflow_actions" not in params:
        return True
    allowed = params.get("allowed_workflow_actions")
    if not isinstance(allowed, list) or not allowed:
        return False
    return action in {str(item) for item in allowed}


def _next_packet(current_packet: str, action: str) -> str:
    if action == "escalate":
        return "escalation_record"
    if current_packet not in _PACKET_ORDER:
        return _PACKET_ORDER[0]
    current_idx = _PACKET_ORDER.index(current_packet)
    if current_idx >= len(_PACKET_ORDER) - 1:
        return _PACKET_ORDER[-1]
    return _PACKET_ORDER[current_idx + 1]


def _resolve_escalation_policy(tier: str, params: dict[str, Any]) -> dict[str, Any]:
    raw_policy = params.get("escalation_policy_by_tier")
    if isinstance(raw_policy, dict):
        candidate = raw_policy.get(tier)
        if isinstance(candidate, dict):
            return {
                "target_role": str(candidate.get("target_role", "manager")),
                "priority": str(candidate.get("priority", "high")),
                "sla_minutes": int(_to_float(candidate.get("sla_minutes"), 15.0)),
            }
    return dict(_DEFAULT_ESCALATION_POLICY.get(tier, _DEFAULT_ESCALATION_POLICY["major"]))


def build_initial_state(profile: dict[str, Any]) -> dict[str, Any]:
    entity_state = profile.get("entity_state") or {}
    return {
        "open_draft_count": int(entity_state.get("open_draft_count", 0)),
        "last_recommendation_tier": entity_state.get("last_recommendation_tier"),
        "workflow_context": {
            "current_packet": "service_intake_packet",
            "next_packet": "estimate_context_packet",
            "connector_instance_id": entity_state.get("connector_instance_id"),
            "connector_thread_id": entity_state.get("connector_thread_id"),
            "escalation_record_id": entity_state.get("escalation_record_id"),
            "last_action": None,
            "last_confidence": None,
        },
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
    confidence = _to_float(evidence.get("confidence_score"), 0.5)
    low_conf_threshold = _to_float(params.get("low_confidence_threshold"), 0.25)

    if high_risk and not approved:
        tier = "major"
        action = "escalate"
    elif confidence < low_conf_threshold:
        tier = "major"
        action = "escalate"
    elif approved:
        tier = "minor"
        action = "stage_erp_draft_update"
        new_state["open_draft_count"] = int(new_state.get("open_draft_count", 0)) + 1
    else:
        tier = "ok"
        action = "recommend_next_step"

    allowlist_blocked = False
    if not _allowlisted(action, params):
        action = "escalate"
        tier = "major"
        allowlist_blocked = True

    workflow_context = dict(new_state.get("workflow_context") or {})
    current_packet = str(
        evidence.get("packet_type")
        or workflow_context.get("current_packet")
        or _PACKET_ORDER[0]
    )
    next_packet = _next_packet(current_packet, action)

    for key in ("connector_instance_id", "connector_thread_id", "escalation_record_id"):
        if key in evidence and evidence.get(key) is not None:
            workflow_context[key] = evidence.get(key)

    workflow_context["current_packet"] = current_packet
    workflow_context["next_packet"] = next_packet
    workflow_context["last_action"] = action
    workflow_context["last_confidence"] = confidence

    new_state["workflow_context"] = workflow_context
    escalation_policy = _resolve_escalation_policy(tier, params)

    new_state["last_recommendation_tier"] = tier
    return new_state, {
        "tier": tier,
        "action": action,
        "escalation_eligible": high_risk,
        "confidence_score": confidence,
        "allowlist_blocked": allowlist_blocked,
        "workflow": {
            "current_packet": current_packet,
            "next_packet": next_packet,
            "dispatch": {
                "handler": _ACTION_TO_HANDLER.get(action, "workflow.intake_or_status"),
                "payload": {
                    "connector_instance_id": workflow_context.get("connector_instance_id"),
                    "connector_thread_id": workflow_context.get("connector_thread_id"),
                    "escalation_record_id": workflow_context.get("escalation_record_id"),
                    "allowlist_blocked": allowlist_blocked,
                },
            },
        },
        "escalation": {
            "target_role": escalation_policy["target_role"],
            "priority": escalation_policy["priority"],
            "sla_minutes": escalation_policy["sla_minutes"],
            "recommended": action == "escalate",
        },
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
