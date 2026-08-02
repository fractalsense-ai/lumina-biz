"""Business-ops auto-repair workflow endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.concurrency import run_in_threadpool

from lumina.api import config as _cfg
from lumina.api.models import AutoRepairWorkflowRequest, AutoRepairWorkflowResponse
from lumina.api.processing import process_message
from lumina.api.session import _session_containers
from lumina.api.middleware import _bearer_scheme, get_current_user

log = logging.getLogger("lumina-api")

router = APIRouter()

_ACTION_TO_HANDLER = {
    "recommend_next_step": "workflow.intake_or_status",
    "stage_erp_draft_update": "workflow.stage_draft_update",
    "escalate": "workflow.escalate_case",
}

_PACKET_ORDER = (
    "service_intake_packet",
    "estimate_context_package",
    "customer_communication_draft",
    "escalation_record",
)

_WORKFLOW_CONTEXTS: dict[str, dict[str, Any]] = {}
_WORKFLOW_DRAFTS: dict[str, dict[str, Any]] = {}


def _get_workflow_context(session_id: str) -> dict[str, Any]:
    container = _session_containers.get(session_id)
    if container is not None:
        return container.active_context.workflow_context
    return _WORKFLOW_CONTEXTS.setdefault(session_id, {})


def _write_workflow_context(session_id: str, context: dict[str, Any]) -> None:
    container = _session_containers.get(session_id)
    if container is not None:
        container.active_context.workflow_context = context
    _WORKFLOW_CONTEXTS[session_id] = context


def _append_session_record(session_id: str, record: dict[str, Any]) -> None:
    _cfg.PERSISTENCE.append_log_record(
        session_id,
        record,
        ledger_path=_cfg.PERSISTENCE.get_system_ledger_path(session_id),
    )


def _next_packet(current_packet: str, action: str) -> str:
    if action == "escalate":
        return "escalation_record"
    if current_packet not in _PACKET_ORDER:
        return _PACKET_ORDER[0]
    idx = _PACKET_ORDER.index(current_packet)
    if idx >= len(_PACKET_ORDER) - 1:
        return _PACKET_ORDER[-1]
    return _PACKET_ORDER[idx + 1]


def _execute_workflow_handler(
    *,
    session_id: str,
    stage: str,
    action: str,
    message: str,
    domain_id: str | None,
    actor_id: str,
) -> dict[str, Any]:
    context = dict(_get_workflow_context(session_id))

    if action == "stage_erp_draft_update":
        draft_id = str(uuid.uuid4())
        staged = {
            "draft_id": draft_id,
            "session_id": session_id,
            "stage": stage,
            "domain_id": domain_id,
            "actor_id": actor_id,
            "message": message,
            "status": "staged",
            "created_utc": datetime.now(timezone.utc).isoformat(),
        }
        _WORKFLOW_DRAFTS[draft_id] = staged
        _append_session_record(
            session_id,
            {
                "event": "workflow_draft_staged",
                "record_type": "WorkflowDraftStage",
                **staged,
            },
        )
        return {
            "type": "draft_staged",
            "draft_id": draft_id,
            "status": "staged",
        }

    if action == "escalate":
        escalation_record_id = str(uuid.uuid4())
        esc_record = {
            "record_type": "EscalationRecord",
            "record_id": escalation_record_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "escalating_actor_id": actor_id,
            "target_meta_authority_id": "manager",
            "trigger": "workflow_auto_repair_escalation",
            "trigger_type": "other",
            "model_pack_id": domain_id or "business-ops",
            "evidence_summary": {
                "stage": stage,
                "action": action,
                "message": message[:200],
            },
            "status": "pending",
        }
        _append_session_record(session_id, esc_record)
        context["escalation_record_id"] = escalation_record_id
        _write_workflow_context(session_id, context)
        return {
            "type": "escalation_recorded",
            "escalation_record_id": escalation_record_id,
            "status": "pending",
        }

    _append_session_record(
        session_id,
        {
            "event": "workflow_step_processed",
            "record_type": "WorkflowStepRecord",
            "session_id": session_id,
            "domain_id": domain_id,
            "actor_id": actor_id,
            "stage": stage,
            "action": action,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {
        "type": "step_processed",
        "status": "ok",
    }


def _workflow_metadata(
    *,
    session_id: str,
    stage: str,
    action: str,
) -> dict[str, Any]:
    context = dict(_get_workflow_context(session_id))
    return {
        "stage": stage,
        "current_packet": context.get("current_packet", "service_intake_packet"),
        "next_packet": context.get("next_packet", "estimate_context_package"),
        "dispatch": {
            "handler": _ACTION_TO_HANDLER.get(action, "workflow.intake_or_status"),
            "payload": {
                "connector_instance_id": context.get("connector_instance_id"),
                "connector_thread_id": context.get("connector_thread_id"),
                "escalation_record_id": context.get("escalation_record_id"),
            },
        },
    }


async def _run_workflow_turn(
    req: AutoRepairWorkflowRequest,
    *,
    stage: str,
    stage_defaults: dict[str, Any],
    credentials: HTTPAuthorizationCredentials | None,
) -> AutoRepairWorkflowResponse:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user = await get_current_user(credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    session_id = req.session_id or str(uuid.uuid4())
    turn_data = dict(req.turn_data_override or {})
    for key, value in stage_defaults.items():
        turn_data.setdefault(key, value)

    context = dict(_get_workflow_context(session_id))
    for key in ("connector_instance_id", "connector_thread_id"):
        if key in turn_data and turn_data[key] is not None:
            context[key] = turn_data[key]
    context["current_packet"] = turn_data.get("packet_type", context.get("current_packet", "service_intake_packet"))
    _write_workflow_context(session_id, context)

    try:
        result = await run_in_threadpool(
            process_message,
            session_id,
            req.message,
            turn_data,
            req.deterministic_response,
            req.domain_id,
            user,
            None,
            None,
            False,
            None,
            None,
            False,
        )
    except Exception as exc:
        log.exception("Workflow step failed (stage=%s, session=%s)", stage, session_id)
        raise HTTPException(status_code=500, detail=str(exc))

    execution = await run_in_threadpool(
        _execute_workflow_handler,
        session_id=session_id,
        stage=stage,
        action=result["action"],
        message=req.message,
        domain_id=result.get("domain_id"),
        actor_id=str(user.get("sub", "")),
    )

    progressed = dict(_get_workflow_context(session_id))
    current_packet = str(progressed.get("current_packet", "service_intake_packet"))
    progressed["next_packet"] = _next_packet(current_packet, result["action"])
    _write_workflow_context(session_id, progressed)

    metadata = _workflow_metadata(session_id=session_id, stage=stage, action=result["action"])
    metadata["execution"] = execution

    return AutoRepairWorkflowResponse(
        session_id=session_id,
        response=result["response"],
        action=result["action"],
        prompt_type=result["prompt_type"],
        escalated=result["escalated"],
        domain_id=result.get("domain_id"),
        tool_results=result.get("tool_results") or None,
        structured_content=result.get("structured_content"),
        workflow=metadata,
    )


@router.post("/api/workflow/auto-repair/intake", response_model=AutoRepairWorkflowResponse)
async def auto_repair_intake(
    req: AutoRepairWorkflowRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AutoRepairWorkflowResponse:
    return await _run_workflow_turn(
        req,
        stage="intake",
        stage_defaults={
            "packet_type": "service_intake_packet",
        },
        credentials=credentials,
    )


@router.post("/api/workflow/auto-repair/status", response_model=AutoRepairWorkflowResponse)
async def auto_repair_status(
    req: AutoRepairWorkflowRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AutoRepairWorkflowResponse:
    return await _run_workflow_turn(
        req,
        stage="status",
        stage_defaults={
            "packet_type": "estimate_context_package",
        },
        credentials=credentials,
    )


@router.post("/api/workflow/auto-repair/draft-update", response_model=AutoRepairWorkflowResponse)
async def auto_repair_draft_update(
    req: AutoRepairWorkflowRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AutoRepairWorkflowResponse:
    return await _run_workflow_turn(
        req,
        stage="draft-update",
        stage_defaults={
            "packet_type": "customer_communication_draft",
            "explicit_approval_language": True,
        },
        credentials=credentials,
    )
