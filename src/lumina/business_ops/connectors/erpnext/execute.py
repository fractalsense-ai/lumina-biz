"""Fixture-only execution seam for the ERPNext Slice 33 connector."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from .errors import normalize_erpnext_error
from .fixtures import DeterministicFixtureRunner
from .mapping import map_operation_to_erpnext


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _canonical_status(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "succeeded":
        return "completed"
    if normalized in {"accepted", "rejected", "pending", "completed", "failed", "cancelled"}:
        return normalized
    return "failed"


def _extract_actor_scope(request: dict[str, object]) -> tuple[str, str, str] | None:
    scope = request.get("actor_scope")
    if not isinstance(scope, dict):
        return None
    organization_id = str(scope.get("organization_id") or "").strip()
    site_id = str(scope.get("site_id") or "").strip()
    actor_id = str(scope.get("actor_id") or "").strip()
    if not organization_id or not site_id or not actor_id:
        return None
    return organization_id, site_id, actor_id


def _scope_error(
    *,
    code: str,
    message: str,
    action_class: str,
    capability_namespace: str,
) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "severity": "critical",
        "retryable": False,
        "action_class": action_class,
        "capability_namespace": capability_namespace,
    }


def execute_with_fixtures(
    request: dict[str, object],
    fixture_runner: DeterministicFixtureRunner,
    *,
    expected_scope: dict[str, str] | None = None,
) -> dict[str, object]:
    """Execute a canonical request through deterministic fixture mode only."""
    request_id = str(request.get("request_id") or "").strip()
    action_class = str(request.get("action_class") or "").strip()
    capability_namespace = str(request.get("capability_namespace") or "").strip()

    result: dict[str, object] = {
        "request_id": request_id,
        "result_id": f"res-{uuid4()}",
        "action_class": action_class,
        "capability_namespace": capability_namespace,
        "status": "failed",
        "occurred_utc": _utc_now(),
    }

    actor_scope = _extract_actor_scope(request)
    if actor_scope is None:
        result["errors"] = [
            _scope_error(
                code="MISSING_ACTOR_SCOPE",
                message="Request must include actor_scope.organization_id, actor_scope.site_id, and actor_scope.actor_id",
                action_class=action_class,
                capability_namespace=capability_namespace,
            )
        ]
        return result

    organization_id, site_id, actor_id = actor_scope
    if expected_scope is not None:
        expected_org = str(expected_scope.get("organization_id") or "").strip()
        expected_site = str(expected_scope.get("site_id") or "").strip()
        if expected_org and organization_id != expected_org:
            result["errors"] = [
                _scope_error(
                    code="SCOPE_MISMATCH",
                    message="organization_id is outside active tenant scope",
                    action_class=action_class,
                    capability_namespace=capability_namespace,
                )
            ]
            return result
        if expected_site and site_id != expected_site:
            result["errors"] = [
                _scope_error(
                    code="SCOPE_MISMATCH",
                    message="site_id is outside active tenant scope",
                    action_class=action_class,
                    capability_namespace=capability_namespace,
                )
            ]
            return result

    result["metadata"] = {
        "actor_scope": {
            "organization_id": organization_id,
            "site_id": site_id,
            "actor_id": actor_id,
        }
    }

    try:
        mapped = map_operation_to_erpnext(request)
    except ValueError as exc:
        result["errors"] = [
            {
                "code": "UNSUPPORTED_MAPPING",
                "message": str(exc),
                "severity": "warning",
                "retryable": False,
                "action_class": action_class,
                "capability_namespace": capability_namespace,
            }
        ]
        return result

    fixture_request = {
        "action_class": action_class,
        "capability_namespace": capability_namespace,
        "erpnext_payload": mapped,
        "actor_scope": {
            "organization_id": organization_id,
            "site_id": site_id,
            "actor_id": actor_id,
        },
    }
    fixture_result = fixture_runner.run(fixture_request)

    status = _canonical_status(str(fixture_result.get("status") or "failed"))
    result["status"] = status

    if status == "failed":
        source_errors = fixture_result.get("errors")
        normalized_errors: list[dict[str, object]] = []
        if isinstance(source_errors, list):
            for error in source_errors:
                if not isinstance(error, dict):
                    continue
                raw_status = error.get("status_code")
                status_code: int | None = None
                if isinstance(raw_status, int):
                    status_code = raw_status
                normalized_errors.append(
                    normalize_erpnext_error(
                        status_code=status_code,
                        message=str(error.get("message") or "ERPNext fixture execution failed"),
                        action_class=action_class,
                        capability_namespace=capability_namespace,
                        provider_error_code=(
                            str(error.get("provider_error_code"))
                            if error.get("provider_error_code") is not None
                            else None
                        ),
                        provider_message=(
                            str(error.get("provider_message"))
                            if error.get("provider_message") is not None
                            else None
                        ),
                        details=(error.get("details") if isinstance(error.get("details"), dict) else None),
                    )
                )
        if not normalized_errors:
            normalized_errors.append(
                normalize_erpnext_error(
                    status_code=None,
                    message="ERPNext fixture execution failed",
                    action_class=action_class,
                    capability_namespace=capability_namespace,
                )
            )
        result["errors"] = normalized_errors
    else:
        if "data" in fixture_result and isinstance(fixture_result["data"], dict):
            result["result_data"] = dict(fixture_result["data"])

    return result
