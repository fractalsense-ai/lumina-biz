"""ERPNext error normalization into canonical connector_error payloads."""

from __future__ import annotations


def normalize_erpnext_error(
    *,
    status_code: int | None,
    message: str,
    action_class: str | None = None,
    capability_namespace: str | None = None,
) -> dict[str, object]:
    """Normalize provider failures to canonical connector_error fields."""
    code = "UPSTREAM_ERROR"
    severity = "error"
    retryable = False

    if status_code == 400:
        code = "VALIDATION_FAILED"
        severity = "warning"
        retryable = False
    elif status_code in (401, 403):
        code = "AUTH_FAILED"
        severity = "critical"
        retryable = False
    elif status_code == 404:
        code = "NOT_FOUND"
        severity = "warning"
        retryable = False
    elif status_code == 429:
        code = "RATE_LIMITED"
        severity = "warning"
        retryable = True
    elif status_code is not None and status_code >= 500:
        code = "UPSTREAM_UNAVAILABLE"
        severity = "error"
        retryable = True

    payload: dict[str, object] = {
        "code": code,
        "message": message.strip() or "ERPNext operation failed",
        "severity": severity,
        "retryable": retryable,
    }
    if action_class:
        payload["action_class"] = action_class
    if capability_namespace:
        payload["capability_namespace"] = capability_namespace
    return payload
