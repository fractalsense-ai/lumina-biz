"""Authenticated, scope-safe connector-routing preflight API."""
from __future__ import annotations

import hashlib
import re

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from lumina.api import config as _cfg
from lumina.api.dependencies import get_active_operating_context, get_authenticated_user
from lumina.api.models import (
    ConnectorExecutionFixtureRequest,
    ConnectorExecutionFixtureResponse,
    ConnectorRoutingPreflightRequest,
    ConnectorRoutingPreflightResponse,
    ERPNextInventoryScanRequest,
    ERPNextInventoryScanResponse,
    InventoryDiscrepancyRequest,
    InventoryDiscrepancyResponse,
)
from lumina.business_ops.connectors.erpnext import (
    DeterministicFixtureRunner,
    FixtureScenario,
    execute_with_fixtures,
)
from lumina.connector_routing.router import (
    CapabilityDeclaration,
    CapabilityRoute,
    CapabilityRoutePolicy,
    ConnectorRegistryEntry,
    resolve_connector,
)
from lumina.system_log.admin_operations import build_trace_event
from lumina.business_ops.inventory_discrepancy import calculate_inventory_discrepancy
from lumina.system_log.commit_guard import requires_log_commit

router = APIRouter()
_SAFE_SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _scan_session_id(
    *,
    caller_session_id: str | None,
    actor_id: str,
    organization_id: str,
    site_id: str,
) -> str:
    if caller_session_id:
        if not _SAFE_SESSION_ID.fullmatch(caller_session_id):
            raise HTTPException(status_code=422, detail="session_id contains unsupported characters")
        return caller_session_id
    identity = f"{organization_id}|{site_id}|{actor_id}".encode("utf-8")
    return "erpnext-scan-" + hashlib.sha256(identity).hexdigest()[:24]


_ALLOWED_ACTION_CLASSES = frozenset({
    "query",
    "create_draft",
    "update_draft",
    "request_commit",
    "request_cancel",
    "sync_event",
})
_ALLOWED_HEALTH_STATUSES = frozenset({"healthy", "degraded", "unhealthy"})


def _fixture_runner() -> DeterministicFixtureRunner:
    return DeterministicFixtureRunner(
        [
            FixtureScenario(
                scenario_id="erpnext-work-order-query",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "service/work-order",
                },
                result_payload={
                    "status": "succeeded",
                    "data": {
                        "records": [
                            {
                                "name": "WO-0001",
                                "status": "Open",
                            }
                        ]
                    },
                },
            ),
            FixtureScenario(
                scenario_id="erpnext-inventory-query",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "inventory",
                },
                result_payload={
                    "status": "succeeded",
                    "data": {
                        "records": [
                            {
                                "item_code": "SKU-1000",
                                "item_name": "Brake Pad",
                            }
                        ]
                    },
                },
            ),
            FixtureScenario(
                scenario_id="erpnext-dispatch-upstream-failure",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "logistics/dispatch",
                },
                result_payload={
                    "status": "failed",
                    "errors": [
                        {
                            "status_code": 503,
                            "provider_error_code": "ERP-503",
                            "provider_message": "ERPNext temporarily unavailable",
                            "message": "Fixture provider failure",
                        }
                    ],
                },
            ),
            FixtureScenario(
                scenario_id="erpnext-inventory-rate-limit",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "inventory",
                    "organization_id": "org-rate-limited",
                    "site_id": "site-rate-limited",
                },
                result_payload={
                    "status": "failed",
                    "errors": [
                        {
                            "status_code": 429,
                            "provider_error_code": "ERP-429",
                            "provider_message": "Too many requests",
                            "message": "Fixture provider failure",
                        }
                    ],
                },
            ),
            FixtureScenario(
                scenario_id="erpnext-scheduling-validation-failure",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "scheduling",
                    "organization_id": "org-validation",
                    "site_id": "site-validation",
                },
                result_payload={
                    "status": "failed",
                    "errors": [
                        {
                            "status_code": 400,
                            "provider_error_code": "ERP-400",
                            "provider_message": "Bad request",
                            "message": "Fixture provider failure",
                        }
                    ],
                },
            ),
            FixtureScenario(
                scenario_id="erpnext-work-order-auth-failure",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "service/work-order",
                    "organization_id": "org-auth",
                    "site_id": "site-auth",
                },
                result_payload={
                    "status": "failed",
                    "errors": [
                        {
                            "status_code": 401,
                            "provider_error_code": "ERP-401",
                            "provider_message": "Unauthorized",
                            "message": "Fixture provider failure",
                        }
                    ],
                },
            ),
        ]
    )


def _normalize_required(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=422, detail=f"{field_name} is required")
    return normalized


def _normalize_action_class(value: str, *, field_name: str) -> str:
    normalized = _normalize_required(value, field_name=field_name).lower()
    if normalized not in _ALLOWED_ACTION_CLASSES:
        raise HTTPException(status_code=422, detail=f"Unsupported action_class '{value}'")
    return normalized


def _normalize_health_status(value: str, *, field_name: str) -> str:
    normalized = _normalize_required(value, field_name=field_name).lower()
    if normalized not in _ALLOWED_HEALTH_STATUSES:
        raise HTTPException(status_code=422, detail=f"Unsupported health_status '{value}'")
    return normalized


def _normalize_action_classes(values: list[str], *, field_name: str) -> tuple[str, ...]:
    normalized = tuple(_normalize_action_class(item, field_name=field_name) for item in values)
    if not normalized:
        raise HTTPException(status_code=422, detail=f"{field_name} must contain at least one action class")
    return normalized


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
    action_class = _normalize_action_class(req.action_class, field_name="action_class")
    capability_namespace = _normalize_required(
        req.capability_namespace,
        field_name="capability_namespace",
    )

    entries: list[ConnectorRegistryEntry] = []
    for entry in req.connector_registry_entries:
        if entry.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="ORGANIZATION_MISMATCH")
        if entry.site_id != site_id:
            raise HTTPException(status_code=403, detail="SITE_MISMATCH")
        connector_instance_id = _normalize_required(
            entry.connector_instance_id,
            field_name="connector_registry_entries.connector_instance_id",
        )
        capability_namespaces = tuple(
            _normalize_required(
                namespace,
                field_name="connector_registry_entries.capability_namespaces",
            )
            for namespace in entry.capability_namespaces
        )
        supported_action_classes = _normalize_action_classes(
            entry.supported_action_classes,
            field_name="connector_registry_entries.supported_action_classes",
        )
        if (
            entry.capabilities is None
            and len(set(capability_namespaces)) > 1
            and len(set(supported_action_classes)) > 1
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "connector_registry_entries.capabilities is required when "
                    "multiple namespaces and actions need exact pairing"
                ),
            )
        capabilities = None
        if entry.capabilities is not None:
            capability_declarations: list[CapabilityDeclaration] = []
            declared_namespaces: set[str] = set()
            for capability in entry.capabilities:
                namespace = _normalize_required(
                    capability.namespace,
                    field_name="connector_registry_entries.capabilities.namespace",
                )
                if namespace in declared_namespaces:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Duplicate capability declaration for '{namespace}'",
                    )
                declared_namespaces.add(namespace)
                capability_declarations.append(
                    CapabilityDeclaration(
                        namespace=namespace,
                        supported_actions=_normalize_action_classes(
                            capability.supported_actions,
                            field_name="connector_registry_entries.capabilities.supported_actions",
                        ),
                    )
                )
            capabilities = tuple(capability_declarations)
            declared_namespaces = {declaration.namespace for declaration in capabilities}
            declared_actions = {
                action
                for declaration in capabilities
                for action in declaration.supported_actions
            }
            if (
                set(capability_namespaces) != declared_namespaces
                or set(supported_action_classes) != declared_actions
            ):
                raise HTTPException(
                    status_code=422,
                    detail="Connector capability summary lists do not match capabilities",
                )
        health_status = _normalize_health_status(
            entry.health_status,
            field_name="connector_registry_entries.health_status",
        )
        entries.append(
            ConnectorRegistryEntry(
                organization_id=entry.organization_id,
                site_id=entry.site_id,
                connector_instance_id=connector_instance_id,
                capability_namespaces=capability_namespaces,
                supported_action_classes=supported_action_classes,
                enabled=entry.enabled,
                health_status=health_status,
                is_site_primary=entry.is_site_primary,
                capabilities=capabilities,
            )
        )

    routes = tuple(
        CapabilityRoute(
            capability_namespace=_normalize_required(
                route.capability_namespace,
                field_name="capability_routes.capability_namespace",
            ),
            connector_instance_id=_normalize_required(
                route.connector_instance_id,
                field_name="capability_routes.connector_instance_id",
            ),
            supported_action_classes=tuple(
                _normalize_action_class(
                    action,
                    field_name="capability_routes.supported_action_classes",
                )
                for action in route.supported_action_classes
            ),
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
            request_id=_normalize_required(req.request_id, field_name="request_id"),
            actor_id=str(user["sub"]),
            action_class=action_class,
            capability_namespace=capability_namespace,
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


@router.post(
    "/api/connectors/erpnext/execute-fixture",
    response_model=ConnectorExecutionFixtureResponse,
)
@requires_log_commit
async def execute_fixture(
    req: ConnectorExecutionFixtureRequest,
    user: dict[str, object] = Depends(get_authenticated_user),
    context: dict[str, str | None] = Depends(get_active_operating_context),
) -> ConnectorExecutionFixtureResponse:
    """Execute canonical operation requests via deterministic ERPNext fixtures.

    This endpoint is fixture-only and enforces strict active org/site boundaries.
    """
    organization_id = str(context["organization_id"])
    site_id = str(context["site_id"])

    if req.actor_scope.organization_id != organization_id:
        raise HTTPException(status_code=403, detail="ORGANIZATION_MISMATCH")
    if req.actor_scope.site_id != site_id:
        raise HTTPException(status_code=403, detail="SITE_MISMATCH")
    if req.actor_scope.actor_id != str(user.get("sub") or ""):
        raise HTTPException(status_code=403, detail="actor_scope.actor_id must match authenticated actor")

    request_payload = {
        "request_id": req.request_id,
        "action_class": _normalize_action_class(req.action_class, field_name="action_class"),
        "capability_namespace": _normalize_required(req.capability_namespace, field_name="capability_namespace"),
        "payload": req.payload,
        "actor_scope": {
            "organization_id": req.actor_scope.organization_id,
            "site_id": req.actor_scope.site_id,
            "actor_id": req.actor_scope.actor_id,
        },
    }

    result = await run_in_threadpool(
        execute_with_fixtures,
        request_payload,
        _fixture_runner(),
        expected_scope={"organization_id": organization_id, "site_id": site_id},
    )

    execution_session_id = req.session_id or "connector-execution"
    trace_event = build_trace_event(
        session_id=execution_session_id,
        actor_id=str(user["sub"]),
        event_type="other",
        decision="connector_fixture_executed",
        evidence_summary={"connector_operation_result": result},
    )
    await run_in_threadpool(
        _cfg.PERSISTENCE.append_log_record,
        execution_session_id,
        trace_event,
        _cfg.PERSISTENCE.get_system_ledger_path(execution_session_id),
    )

    return ConnectorExecutionFixtureResponse(**result)


@router.post(
    "/api/connectors/erpnext/scan",
    response_model=ERPNextInventoryScanResponse,
)
@requires_log_commit
async def execute_erpnext_inventory_scan(
    req: ERPNextInventoryScanRequest,
    user: dict[str, object] = Depends(get_authenticated_user),
    context: dict[str, str | None] = Depends(get_active_operating_context),
) -> ERPNextInventoryScanResponse:
    """Resolve a barcode, serial, batch, or warehouse through ERPNext read-only lookup."""
    organization_id = str(context["organization_id"])
    site_id = str(context["site_id"])
    if not req.search_value.strip():
        raise HTTPException(status_code=422, detail="search_value must not be whitespace")
    scan_session_id = _scan_session_id(
        caller_session_id=req.session_id,
        actor_id=str(user["sub"]),
        organization_id=organization_id,
        site_id=site_id,
    )
    adapter = getattr(_cfg, "ERPNext_INVENTORY_SCAN_ADAPTER", None)
    if adapter is None:
        raise HTTPException(status_code=503, detail="ERPNext inventory scan is not configured")

    result = await run_in_threadpool(
        adapter.lookup,
        req.search_value,
        organization_id=organization_id,
        site_id=site_id,
    )

    trace_event = build_trace_event(
        session_id=scan_session_id,
        actor_id=str(user["sub"]),
        event_type="other",
        decision="erpnext_inventory_scan_evaluated",
        evidence_summary={
            "status_code": result.status_code,
            "correlation_id": result.correlation_id,
            "attempts": result.attempts,
            "error_code": result.error.get("code") if result.error else None,
        },
    )
    await run_in_threadpool(
        _cfg.PERSISTENCE.append_linked_log_record,
        scan_session_id,
        trace_event,
        _cfg.PERSISTENCE.get_system_ledger_path(scan_session_id),
    )

    return ERPNextInventoryScanResponse(
        status_code=result.status_code,
        correlation_id=result.correlation_id,
        attempts=result.attempts,
        payload=result.payload,
        error=result.error,
    )


@router.post(
    "/api/connectors/inventory/discrepancy",
    response_model=InventoryDiscrepancyResponse,
)
@requires_log_commit
async def calculate_inventory_discrepancy_review(
    req: InventoryDiscrepancyRequest,
    user: dict[str, object] = Depends(get_authenticated_user),
    context: dict[str, str | None] = Depends(get_active_operating_context),
) -> InventoryDiscrepancyResponse:
    """Create deterministic discrepancy review evidence without posting stock."""
    try:
        result_data = calculate_inventory_discrepancy(
            item_code=req.item_code,
            warehouse=req.warehouse,
            counted_qty=req.counted_qty,
            on_hand_qty=req.on_hand_qty,
            valuation_rate=req.valuation_rate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    scan_session_id = _scan_session_id(
        caller_session_id=req.session_id,
        actor_id=str(user["sub"]),
        organization_id=str(context["organization_id"]),
        site_id=str(context["site_id"]),
    )
    trace_event = build_trace_event(
        session_id=scan_session_id,
        actor_id=str(user["sub"]),
        event_type="discrepancy_detected" if result_data["review_required"] else "inventory_count_matched",
        decision="inventory_discrepancy_review",
        evidence_summary={
            "item_code": result_data["item_code"],
            "warehouse": result_data["warehouse"],
            "variance_qty": result_data["variance_qty"],
            "review_required": result_data["review_required"],
            "stock_mutation_requested": False,
        },
    )
    await run_in_threadpool(
        _cfg.PERSISTENCE.append_linked_log_record,
        scan_session_id,
        trace_event,
        _cfg.PERSISTENCE.get_system_ledger_path(scan_session_id),
    )

    return InventoryDiscrepancyResponse(
        status="pending" if result_data["review_required"] else "completed",
        result_data=result_data,
    )
