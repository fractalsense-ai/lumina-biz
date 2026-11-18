from __future__ import annotations

from dataclasses import replace

import httpx
import pytest

from lumina.business_ops.connectors.transport import (
    ConnectorTransportRequest,
    TransportPolicy,
    send_json,
)


def _request(action_class: str = "query") -> ConnectorTransportRequest:
    return ConnectorTransportRequest(
        method="POST",
        url="https://erp.example.test/api/resource/Item",
        payload={"filters": {"disabled": False}},
        action_class=action_class,
        capability_namespace="inventory",
        correlation_id="corr-1",
        idempotency_key="idem-1" if action_class != "query" else None,
    )


@pytest.mark.unit
def test_query_retries_transient_status_and_propagates_correlation() -> None:
    attempts = 0
    observed_headers: list[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        observed_headers.append(request.headers)
        if attempts == 1:
            return httpx.Response(503, json={"message": "temporary"})
        return httpx.Response(200, json={"data": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = send_json(
            _request(),
            client=client,
            policy=TransportPolicy(timeout_seconds=1, max_query_retries=1),
        )

    assert result.status_code == 200
    assert result.payload == {"data": []}
    assert result.attempts == 2
    assert all(headers["X-Correlation-ID"] == "corr-1" for headers in observed_headers)
    assert "Idempotency-Key" not in observed_headers[0]


@pytest.mark.unit
def test_mutation_is_not_retried_and_propagates_idempotency() -> None:
    attempts = 0
    observed_headers: list[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        observed_headers.append(request.headers)
        return httpx.Response(503, json={"message": "unknown outcome"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = send_json(
            replace(
                _request("request_commit"),
                headers={
                    "x-correlation-id": "caller-correlation",
                    "IDEMPOTENCY-KEY": "caller-idem",
                },
            ),
            client=client,
            policy=TransportPolicy(timeout_seconds=1, max_query_retries=3),
        )

    assert attempts == 1
    assert result.attempts == 1
    assert result.error is not None
    assert result.error["code"] == "UPSTREAM_UNAVAILABLE"
    assert result.error["retryable"] is False
    assert observed_headers[0]["Idempotency-Key"] == "idem-1"
    assert observed_headers[0]["X-Correlation-ID"] == "corr-1"


@pytest.mark.unit
def test_query_timeout_retries_then_returns_canonical_error() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("upstream timeout")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = send_json(
            _request(),
            client=client,
            policy=TransportPolicy(timeout_seconds=1, max_query_retries=1),
        )

    assert attempts == 2
    assert result.status_code is None
    assert result.error is not None
    assert result.error["code"] == "UPSTREAM_UNAVAILABLE"
    assert result.error["retryable"] is True
    assert result.error["details"] == {"attempts": 2, "correlation_id": "corr-1"}


@pytest.mark.unit
def test_auth_failure_is_normalized_without_retry() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(401, json={"message": "do not log credentials"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = send_json(
            _request(),
            client=client,
            policy=TransportPolicy(timeout_seconds=1, max_query_retries=2),
        )

    assert attempts == 1
    assert result.error is not None
    assert result.error["code"] == "AUTH_FAILED"
    assert result.error["retryable"] is False
    assert "do not log credentials" not in result.error["message"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "status_code,expected_code,expected_retryable",
    [
        (400, "VALIDATION_FAILED", False),
        (401, "AUTH_FAILED", False),
        (404, "NOT_FOUND", False),
        (409, "CONFLICT", False),
        (429, "RATE_LIMITED", True),
        (503, "UPSTREAM_UNAVAILABLE", True),
    ],
)
def test_query_status_error_matrix(status_code, expected_code, expected_retryable) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"message": "provider detail"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = send_json(
            _request(),
            client=client,
            policy=TransportPolicy(timeout_seconds=1, max_query_retries=0),
        )

    assert result.error is not None
    assert result.error["code"] == expected_code
    assert result.error["retryable"] is expected_retryable
    assert "provider detail" not in result.error["message"]


@pytest.mark.unit
@pytest.mark.parametrize("body", [b"not-json", b"[]", b"null"])
def test_malformed_success_response_is_normalized(body: bytes) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = send_json(_request(), client=client)

    assert result.error is not None
    assert result.error["code"] == "MALFORMED_RESPONSE"
    assert result.error["retryable"] is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "kwargs",
    [
        {"timeout_seconds": 0},
        {"timeout_seconds": 61},
        {"max_query_retries": -1},
        {"max_query_retries": 6},
    ],
)
def test_transport_policy_rejects_out_of_range_values(kwargs) -> None:
    with pytest.raises(ValueError):
        TransportPolicy(**kwargs)