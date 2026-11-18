from __future__ import annotations

import json
import logging

import httpx
import pytest

from lumina.auth.actor_liveness import (
    ACTOR_INACTIVE,
    ACTOR_MALFORMED,
    ACTOR_UNAVAILABLE,
    ActorLivenessResult,
)
from lumina.business_ops.connectors.erpnext.liveness import ERPNextActorLivenessAdapter
from lumina.business_ops.connectors.transport import TransportPolicy


def _claims() -> dict[str, str]:
    return {
        "sub": "actor@example.test",
        "organization_id": "org-1",
        "site_id": "site-1",
        "iss": "lumina-erp",
        "jti": "verified-jti",
    }


def _adapter(client: httpx.Client, *, auth_header_provider=lambda: "token api-key:api-secret"):
    return ERPNextActorLivenessAdapter(
        base_url="https://erp.example.test/",
        expected_organization_id="org-1",
        expected_site_id="site-1",
        authorization_header_provider=auth_header_provider,
        client=client,
        policy=TransportPolicy(timeout_seconds=1, max_query_retries=1),
    )


@pytest.mark.unit
def test_erpnext_liveness_adapter_is_exported_from_connector_package() -> None:
    from lumina.business_ops.connectors.erpnext import ERPNextActorLivenessAdapter as exported_adapter

    assert exported_adapter is ERPNextActorLivenessAdapter


@pytest.mark.unit
def test_erpnext_liveness_reads_only_user_enabled_fields() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"data": [{"name": "actor@example.test", "enabled": 1}]},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _adapter(client)(_claims())

    assert result == ActorLivenessResult(
        allow=True,
        deny_reason=None,
        evidence_code="user_enabled",
    )
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "GET"
    assert request.url.path == "/api/resource/User"
    assert json.loads(request.url.params["filters"]) == [
        ["User", "name", "=", "actor@example.test"],
    ]
    assert json.loads(request.url.params["fields"]) == ["name", "enabled"]
    assert request.url.params["limit_page_length"] == "1"
    assert request.content == b""
    assert request.headers["Authorization"] == "token api-key:api-secret"


@pytest.mark.unit
@pytest.mark.parametrize(
    "body,evidence_code",
    [
        ({"data": []}, "user_record_missing"),
        ({"data": [{"name": "actor@example.test", "enabled": 0}]}, "user_disabled"),
    ],
)
def test_erpnext_liveness_denies_missing_or_disabled_user(body, evidence_code) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _adapter(client)(_claims())

    assert result.allow is False
    assert result.deny_reason == ACTOR_INACTIVE
    assert result.evidence_code == evidence_code


@pytest.mark.unit
def test_erpnext_liveness_maps_collection_not_found_to_unavailable() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "resource unavailable"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _adapter(client)(_claims())

    assert result.allow is False
    assert result.deny_reason == ACTOR_UNAVAILABLE
    assert result.evidence_code == "transport_not_found"


@pytest.mark.unit
def test_erpnext_liveness_maps_secret_provider_failure_to_unavailable() -> None:
    def _missing_credentials() -> str:
        raise RuntimeError("secret store unavailable")

    with httpx.Client(transport=httpx.MockTransport(lambda _request: pytest.fail("must not call upstream"))) as client:
        result = _adapter(client, auth_header_provider=_missing_credentials)(_claims())

    assert result.allow is False
    assert result.deny_reason == ACTOR_UNAVAILABLE
    assert result.evidence_code == "credentials_unavailable"


@pytest.mark.unit
def test_erpnext_liveness_denies_malformed_user_record() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"name": "actor@example.test", "enabled": "yes"}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _adapter(client)(_claims())

    assert result.allow is False
    assert result.deny_reason == ACTOR_MALFORMED
    assert result.evidence_code == "user_enabled_malformed"


@pytest.mark.unit
def test_erpnext_liveness_maps_transport_failure_to_unavailable() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("upstream timeout")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _adapter(client)(_claims())

    assert result.allow is False
    assert result.deny_reason == ACTOR_UNAVAILABLE
    assert result.evidence_code == "transport_upstream_unavailable"


@pytest.mark.unit
def test_erpnext_liveness_requires_actor_and_operating_scope() -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda _request: pytest.fail("must not call upstream"))) as client:
        result = _adapter(client)({"sub": "actor@example.test"})

    assert result.allow is False
    assert result.deny_reason == ACTOR_MALFORMED
    assert result.evidence_code == "actor_scope_malformed"


@pytest.mark.unit
@pytest.mark.parametrize(
    "scope_claim,other_scope",
    [("organization_id", "org-2"), ("site_id", "site-2")],
)
def test_erpnext_liveness_rejects_actor_from_another_scope(scope_claim, other_scope) -> None:
    claims = _claims()
    claims[scope_claim] = other_scope

    with httpx.Client(transport=httpx.MockTransport(lambda _request: pytest.fail("must not call upstream"))) as client:
        result = _adapter(client)(claims)

    assert result.allow is False
    assert result.deny_reason == ACTOR_MALFORMED
    assert result.evidence_code == "actor_scope_mismatch"


@pytest.mark.unit
def test_erpnext_liveness_suppresses_actor_identifier_in_httpx_info_logs(caplog) -> None:
    from lumina.api import server as api_server

    caplog.set_level(logging.INFO)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"name": "actor@example.test", "enabled": 1}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = _adapter(client)(_claims())

    assert result.allow is True
    assert api_server.logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
    assert not any(
        record.name == "httpx" and "actor@example.test" in record.getMessage()
        for record in caplog.records
    )