"""Read-only ERPNext actor-liveness adapter using the generic transport seam."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json
from typing import Any
from uuid import uuid4

import httpx

from lumina.auth.actor_liveness import (
    ACTOR_INACTIVE,
    ACTOR_MALFORMED,
    ACTOR_UNAVAILABLE,
    ActorLivenessResult,
)
from lumina.business_ops.connectors.transport import (
    ConnectorTransportRequest,
    TransportPolicy,
    send_json,
)


class ERPNextActorLivenessAdapter:
    """Check Frappe User.enabled without logging or persisting provider payloads."""

    def __init__(
        self,
        *,
        base_url: str,
        expected_organization_id: str,
        expected_site_id: str,
        authorization_header_provider: Callable[[], str],
        client: httpx.Client,
        policy: TransportPolicy = TransportPolicy(),
    ) -> None:
        normalized_base_url = base_url.strip().rstrip("/")
        if not normalized_base_url.startswith(("http://", "https://")):
            raise ValueError("ERPNext base_url must use HTTP or HTTPS")
        if not isinstance(expected_organization_id, str) or not expected_organization_id.strip():
            raise ValueError("expected_organization_id must be a non-empty string")
        if not isinstance(expected_site_id, str) or not expected_site_id.strip():
            raise ValueError("expected_site_id must be a non-empty string")
        if not callable(authorization_header_provider):
            raise ValueError("authorization_header_provider must be callable")
        self._base_url = normalized_base_url
        self._expected_organization_id = expected_organization_id.strip()
        self._expected_site_id = expected_site_id.strip()
        self._authorization_header_provider = authorization_header_provider
        self._client = client
        self._policy = policy

    def __call__(self, claims: Mapping[str, Any]) -> ActorLivenessResult:
        actor_id = claims.get("sub")
        organization_id = claims.get("organization_id")
        site_id = claims.get("site_id")
        if not all(isinstance(value, str) and value.strip() for value in (actor_id, organization_id, site_id)):
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_MALFORMED,
                evidence_code="actor_scope_malformed",
            )
        if (
            organization_id.strip() != self._expected_organization_id
            or site_id.strip() != self._expected_site_id
        ):
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_MALFORMED,
                evidence_code="actor_scope_mismatch",
            )

        try:
            authorization = self._authorization_header_provider()
        except Exception:
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_UNAVAILABLE,
                evidence_code="credentials_unavailable",
            )
        if not isinstance(authorization, str) or not authorization.strip():
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_UNAVAILABLE,
                evidence_code="credentials_unavailable",
            )

        request = ConnectorTransportRequest(
            method="GET",
            url=f"{self._base_url}/api/resource/User",
            payload={},
            action_class="query",
            capability_namespace=None,
            correlation_id=f"actor-liveness-{uuid4().hex}",
            headers={"Authorization": authorization},
            query_params={
                "filters": f'[["User","name","=",{_json_string(actor_id.strip())}]]',
                "fields": '["name","enabled"]',
                "limit_page_length": "1",
            },
        )
        response = send_json(request, client=self._client, policy=self._policy)
        if response.error is not None:
            if response.error.get("code") == "MALFORMED_RESPONSE":
                return ActorLivenessResult(
                    allow=False,
                    deny_reason=ACTOR_MALFORMED,
                    evidence_code="user_response_malformed",
                )
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_UNAVAILABLE,
                evidence_code="transport_" + _safe_code(response.error.get("code")),
            )

        data = response.payload.get("data") if response.payload is not None else None
        if not isinstance(data, list):
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_MALFORMED,
                evidence_code="user_response_malformed",
            )
        if not data:
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_INACTIVE,
                evidence_code="user_record_missing",
            )
        record = data[0]
        if not isinstance(record, dict) or record.get("name") != actor_id.strip():
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_MALFORMED,
                evidence_code="user_identity_mismatch",
            )

        enabled = record.get("enabled")
        if type(enabled) is bool:
            is_enabled = enabled
        elif type(enabled) is int and enabled in (0, 1):
            is_enabled = bool(enabled)
        else:
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_MALFORMED,
                evidence_code="user_enabled_malformed",
            )
        if not is_enabled:
            return ActorLivenessResult(
                allow=False,
                deny_reason=ACTOR_INACTIVE,
                evidence_code="user_disabled",
            )
        return ActorLivenessResult(
            allow=True,
            deny_reason=None,
            evidence_code="user_enabled",
        )


def _json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _safe_code(value: object) -> str:
    code = str(value or "upstream_error").lower()
    normalized = "".join(character if character.isalnum() or character == "_" else "_" for character in code)
    return normalized[:48] or "upstream_error"