"""Authenticated, scope-safe connector-routing preflight API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from lumina.api import config as _cfg
from lumina.api.dependencies import get_active_operating_context, get_authenticated_user
from lumina.api.models import (
    ConnectorRoutingPreflightRequest,
    ConnectorRoutingPreflightResponse,
)
from lumina.connector_routing.router import (
    CapabilityRoute,
    CapabilityRoutePolicy,
    ConnectorRegistryEntry,
    resolve_connector,
)
from lumina.system_log.admin_operations import build_trace_event
from lumina.system_log.commit_guard import requires_log_commit

router = APIRouter()


def _response_from_record(record: dict[str, object]) -> ConnectorRoutingPreflightResponse:
    return ConnectorRoutingPreflightResponse(
        resolution_id=str(record["resolution_id"]),
        request_id=str(record["request_id"]),
        organization_id=str(record["organization_id"]),
        site_id=str(record["site_id"]),
        actor_id=str(record["actor_id"]),
        action_class=str(record["action_class"]),
        capability_namespace=str(record["capability_namespace"]),
        status=str(record["status"]),
        source=str(record["source"]),
        reason_code=str(record["reason_code"]),
        connector_instance_id=(
            str(record["connector_instance_id"])
            if isinstance(record["connector_instance_id"], str)
            else None
        ),
        idempotency_key=(
            str(record["idempotency_key"]) if isinstance(record["idempotency_key"], str) else None
        ),
        correlation_id=(
            str(record["correlation_id"]) if isinstance(record["correlation_id"], str) else None
        ),
        policy_version=int(record["policy_version"]),
        candidate_connector_ids=[str(v) for v in record["candidate_connector_ids"]],  # type: ignore[index]
        evaluated_utc=str(record["evaluated_utc"]),
    )


@router.post("/api/connector-routing/preflight", response_model=ConnectorRoutingPreflightResponse)
@requires_log_commit
async def preflight(
    req: ConnectorRoutingPreflightRequest,
    user: dict[str, object] = Depends(get_authenticated_user),
    context: dict[str, str | None] = Depends(get_active_operating_context),
) -> ConnectorRoutingPreflightResponse:
    """Resolve a scoped connector target and append transcript-free audit evidence."""
    organization_id = str(context["organization_id"])
    site_id = str(context["site_id"])

    entries: list[ConnectorRegistryEntry] = []
    for entry in req.connector_registry_entries:
        if entry.organization_id != organization_id or entry.site_id != site_id:
            raise HTTPException(status_code=403, detail="Connector registry entry is outside active context")
        entries.append(
            ConnectorRegistryEntry(
                organization_id=entry.organization_id,
                site_id=entry.site_id,
                connector_instance_id=entry.connector_instance_id,
                capability_namespaces=tuple(entry.capability_namespaces),
                supported_action_classes=tuple(entry.supported_action_classes),  # type: ignore[arg-type]
                enabled=entry.enabled,
                health_status=entry.health_status,  # type: ignore[arg-type]
                is_site_primary=entry.is_site_primary,
            )
        )

    routes = tuple(
        CapabilityRoute(
            capability_namespace=route.capability_namespace,
            connector_instance_id=route.connector_instance_id,
            supported_action_classes=tuple(route.supported_action_classes),  # type: ignore[arg-type]
            priority=route.priority,
        )
        for route in req.capability_routes
    )
    policy = CapabilityRoutePolicy(
        policy_version=req.policy_version,
        organization_id=organization_id,
        site_id=site_id,
        routes=routes,
        organization_default_connector_id=req.organization_default_connector_id,
    )

    try:
        result = await run_in_threadpool(
            resolve_connector,
            entries,
            policy,
            request_id=req.request_id,
            actor_id=str(user["sub"]),
            action_class=req.action_class,
            capability_namespace=req.capability_namespace,
            operation_override_connector_id=req.operation_override_connector_id,
            idempotency_key=req.idempotency_key,
            correlation_id=req.correlation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    record = result.as_record()
    routing_session_id = req.session_id or "connector-routing"
    trace_event = build_trace_event(
        session_id=routing_session_id,
        actor_id=str(user["sub"]),
        event_type="other",
        decision="connector_routing_evaluated",
        evidence_summary={"connector_resolution_result": record},
    )
    await run_in_threadpool(
        _cfg.PERSISTENCE.append_log_record,
        routing_session_id,
        trace_event,
        _cfg.PERSISTENCE.get_system_ledger_path(routing_session_id),
    )
    return _response_from_record(record)
