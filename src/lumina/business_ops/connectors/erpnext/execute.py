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


def execute_with_fixtures(
    request: dict[str, object],
    fixture_runner: DeterministicFixtureRunner,
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
                normalized_errors.append(
                    normalize_erpnext_error(
                        status_code=None,
                        message=str(error.get("message") or "ERPNext fixture execution failed"),
                        action_class=action_class,
                        capability_namespace=capability_namespace,
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
