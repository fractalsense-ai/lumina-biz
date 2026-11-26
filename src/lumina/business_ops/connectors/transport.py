"""Provider-neutral outbound HTTP transport for business connectors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx

_ACTION_CLASSES = frozenset(
    {
        "query",
        "create_draft",
        "update_draft",
        "request_commit",
        "request_cancel",
        "sync_event",
    }
)
_MUTATION_ACTIONS = frozenset(
    {"create_draft", "update_draft", "request_commit", "request_cancel", "sync_event"}
)
_RETRYABLE_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class TransportPolicy:
    timeout_seconds: float = 5.0
    max_query_retries: int = 1

    def __post_init__(self) -> None:
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be greater than 0 and at most 60")
        if not 0 <= self.max_query_retries <= 5:
            raise ValueError("max_query_retries must be between 0 and 5")


@dataclass(frozen=True)
class ConnectorTransportRequest:
    method: str
    url: str
    payload: dict[str, Any]
    action_class: str
    capability_namespace: str | None
    correlation_id: str
    headers: Mapping[str, str] | None = None
    idempotency_key: str | None = None
    query_params: Mapping[str, str] | None = None


@dataclass(frozen=True)
class ConnectorTransportResponse:
    status_code: int | None
    payload: dict[str, Any] | None
    correlation_id: str
    attempts: int
    error: dict[str, Any] | None = None


def _error(
    request: ConnectorTransportRequest,
    *,
    code: str,
    message: str,
    severity: str,
    retryable: bool,
    attempts: int,
    status_code: int | None = None,
) -> ConnectorTransportResponse:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "severity": severity,
        "retryable": retryable,
        "action_class": request.action_class,
        "capability_namespace": request.capability_namespace,
        "details": {
            "attempts": attempts,
            "correlation_id": request.correlation_id,
        },
    }
    return ConnectorTransportResponse(
        status_code=status_code,
        payload=None,
        correlation_id=request.correlation_id,
        attempts=attempts,
        error=error,
    )


def transport_error_response(
    request: ConnectorTransportRequest,
    *,
    code: str,
    message: str,
    severity: str,
    retryable: bool = False,
    status_code: int | None = None,
) -> ConnectorTransportResponse:
    """Build a canonical transport error before an HTTP request is sent."""
    return _error(
        request,
        code=code,
        message=message,
        severity=severity,
        retryable=retryable,
        attempts=0,
        status_code=status_code,
    )


def _error_for_status(
    request: ConnectorTransportRequest,
    *,
    status_code: int,
    attempts: int,
) -> ConnectorTransportResponse:
    if status_code in (400, 422):
        code, severity, message = "VALIDATION_FAILED", "warning", "Connector request was rejected"
    elif status_code in (401, 403):
        code, severity, message = "AUTH_FAILED", "critical", "Connector authentication or authorization failed"
    elif status_code == 404:
        code, severity, message = "NOT_FOUND", "warning", "Connector resource was not found"
    elif status_code == 409:
        code, severity, message = "CONFLICT", "warning", "Connector reported a conflict"
    elif status_code == 429:
        code, severity, message = "RATE_LIMITED", "warning", "Connector rate limit was reached"
    elif status_code >= 500:
        code, severity, message = "UPSTREAM_UNAVAILABLE", "error", "Connector service is unavailable"
    else:
        code, severity, message = "UPSTREAM_ERROR", "error", "Connector request failed"

    return _error(
        request,
        code=code,
        message=message,
        severity=severity,
        retryable=(request.action_class == "query" and status_code in _RETRYABLE_STATUSES),
        attempts=attempts,
        status_code=status_code,
    )


def _request_headers(request: ConnectorTransportRequest) -> dict[str, str]:
    headers = {
        key: value
        for key, value in (request.headers or {}).items()
        if key.lower() not in {"x-correlation-id", "idempotency-key"}
    }
    headers["X-Correlation-ID"] = request.correlation_id
    if request.action_class in _MUTATION_ACTIONS and request.idempotency_key:
        headers["Idempotency-Key"] = request.idempotency_key
    return headers


def send_json(
    request: ConnectorTransportRequest,
    *,
    client: httpx.Client,
    policy: TransportPolicy = TransportPolicy(),
) -> ConnectorTransportResponse:
    """Send one JSON connector request with query-only retries and safe metadata."""
    method = request.method.strip().upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        raise ValueError("unsupported connector HTTP method")
    if not request.url.strip() or not request.correlation_id.strip():
        raise ValueError("connector request requires URL and correlation_id")
    if request.action_class not in _ACTION_CLASSES:
        raise ValueError("unsupported connector action_class")
    if request.action_class in _MUTATION_ACTIONS and method == "GET":
        raise ValueError("mutation connector actions cannot use GET")

    max_attempts = 1 + (policy.max_query_retries if request.action_class == "query" else 0)
    headers = _request_headers(request)
    for attempt in range(1, max_attempts + 1):
        try:
            request_options: dict[str, Any] = {
                "headers": headers,
                "timeout": policy.timeout_seconds,
            }
            if method == "GET":
                if request.payload:
                    raise ValueError("GET connector requests must use query_params, not a JSON body")
                request_options["params"] = request.query_params
            else:
                request_options["json"] = request.payload
            outbound = client.build_request(method, request.url, **request_options)
            if request.action_class not in _MUTATION_ACTIONS or not request.idempotency_key:
                if "Idempotency-Key" in outbound.headers:
                    del outbound.headers["Idempotency-Key"]
            response = client.send(outbound, follow_redirects=False)
        except httpx.RequestError:
            if attempt < max_attempts:
                continue
            return _error(
                request,
                code="UPSTREAM_UNAVAILABLE",
                message="Connector transport failed or timed out",
                severity="error",
                retryable=request.action_class == "query",
                attempts=attempt,
            )

        if response.status_code in _RETRYABLE_STATUSES and attempt < max_attempts:
            continue
        if not response.is_success:
            return _error_for_status(
                request,
                status_code=response.status_code,
                attempts=attempt,
            )
        if not response.content:
            return ConnectorTransportResponse(
                status_code=response.status_code,
                payload={},
                correlation_id=request.correlation_id,
                attempts=attempt,
            )
        try:
            payload = response.json()
        except ValueError:
            return _error(
                request,
                code="MALFORMED_RESPONSE",
                message="Connector response was not valid JSON",
                severity="error",
                retryable=False,
                attempts=attempt,
                status_code=response.status_code,
            )
        if not isinstance(payload, dict):
            return _error(
                request,
                code="MALFORMED_RESPONSE",
                message="Connector response must be a JSON object",
                severity="error",
                retryable=False,
                attempts=attempt,
                status_code=response.status_code,
            )
        return ConnectorTransportResponse(
            status_code=response.status_code,
            payload=payload,
            correlation_id=request.correlation_id,
            attempts=attempt,
        )

    raise RuntimeError("connector transport exhausted without a result")