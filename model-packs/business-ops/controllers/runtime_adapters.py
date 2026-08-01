from __future__ import annotations

import json
from typing import Any, Callable


_PACKET_ORDER = (
    "service_intake_packet",
    "estimate_context_packet",
    "status_lookup_packet",
    "customer_communication_draft_packet",
)


def _next_packet(packet_type: str) -> str:
    try:
        idx = _PACKET_ORDER.index(packet_type)
    except ValueError:
        return _PACKET_ORDER[0]
    if idx + 1 >= len(_PACKET_ORDER):
        return _PACKET_ORDER[-1]
    return _PACKET_ORDER[idx + 1]


def _allowlisted(
    params: dict[str, Any],
    *,
    capability_namespace: str,
    action_class: str,
) -> bool:
    allow_cfg = params.get("connector_allowlist_defaults") or {}
    allowed_capabilities = {str(v).strip() for v in (allow_cfg.get("capabilities") or []) if str(v).strip()}
    allowed_action_classes = {str(v).strip() for v in (allow_cfg.get("action_classes") or []) if str(v).strip()}

    if not allowed_capabilities or not allowed_action_classes:
        return True
    return capability_namespace in allowed_capabilities and action_class in allowed_action_classes


def _confidence_threshold(params: dict[str, Any]) -> float:
    threshold = params.get("require_confirmation_threshold")
    if threshold is None:
        threshold = (params.get("confidence_profile_defaults") or {}).get("confirmation_threshold")
    try:
        return float(threshold) if threshold is not None else 0.70
    except (TypeError, ValueError):
        return 0.70


def build_initial_state(profile: dict[str, Any]) -> dict[str, Any]:
    entity_state = profile.get("entity_state") or {}
    return {
        "open_draft_count": int(entity_state.get("open_draft_count", 0)),
        "last_recommendation_tier": entity_state.get("last_recommendation_tier"),
        "turn_count": 0,
        "workflow_packet_type": "service_intake_packet",
    }


def domain_step(
    state: dict[str, Any],
    task_spec: dict[str, Any],
    evidence: dict[str, Any],
    params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    new_state = dict(state)
    new_state.setdefault("open_draft_count", 0)
    new_state.setdefault("last_recommendation_tier", None)
    new_state["turn_count"] = int(new_state.get("turn_count", 0)) + 1

    high_risk = bool(evidence.get("contains_high_risk_terms", False))
    approved = bool(evidence.get("explicit_approval_language", False))
    confidence_score = float(evidence.get("confidence_score") or 0.0)

    packet_explicit = "workflow_packet_type" in evidence or "workflow_packet_type" in new_state
    packet_type = str(
        evidence.get("workflow_packet_type")
        or new_state.get("workflow_packet_type")
        or "service_intake_packet"
    )
    if packet_type not in _PACKET_ORDER:
        packet_type = "service_intake_packet"

    if approved and not packet_explicit:
        capability_namespace = "service/work-order"
        action_class = "update_draft"
        action = "stage_erp_draft_update"
        tier = "minor"
        new_state["open_draft_count"] = int(new_state.get("open_draft_count", 0)) + 1
    elif packet_type == "customer_communication_draft_packet":
        capability_namespace = "service/work-order"
        if approved:
            action_class = "update_draft"
            action = "stage_erp_draft_update"
            tier = "minor"
            new_state["open_draft_count"] = int(new_state.get("open_draft_count", 0)) + 1
        else:
            action_class = "query"
            action = "recommend_next_step"
            tier = "major"
    else:
        capability_namespace = "service/work-order"
        action_class = "query"
        action = "recommend_next_step"
        tier = "ok"
        if confidence_score < _confidence_threshold(params):
            tier = "minor"

    if high_risk and not approved:
        tier = "major"
        action = "escalate"
        capability_namespace = ""
        action_class = ""
    elif action != "escalate" and not _allowlisted(
        params,
        capability_namespace=capability_namespace,
        action_class=action_class,
    ):
        tier = "major"
        action = "escalate"
        capability_namespace = ""
        action_class = ""

    next_packet = packet_type if action == "escalate" else _next_packet(packet_type)
    new_state["workflow_packet_type"] = next_packet

    new_state["last_recommendation_tier"] = tier
    return new_state, {
        "tier": tier,
        "action": action,
        "escalation_eligible": high_risk,
        "workflow_packet_type": packet_type,
        "next_workflow_packet_type": next_packet,
        "capability_namespace": capability_namespace or None,
        "action_class": action_class or None,
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
