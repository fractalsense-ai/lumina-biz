"""Permission-checked ERPNext inventory scan lookup adapter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from uuid import uuid4

import httpx

from lumina.business_ops.connectors.transport import (
    ConnectorTransportRequest,
    ConnectorTransportResponse,
    TransportPolicy,
    send_json,
    transport_error_response,
)


class ERPNextInventoryScanAdapter:
    """Resolve barcode, serial, batch, or warehouse scans through ERPNext."""

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

    def lookup(
        self,
        search_value: str,
        *,
        organization_id: str,
        site_id: str,
    ) -> ConnectorTransportResponse:
        """Call ERPNext's permission-checked scan method without mutating stock."""
        if not isinstance(search_value, str) or not search_value.strip():
            raise ValueError("search_value must be a non-empty string")
        request = ConnectorTransportRequest(
            method="GET",
            url=f"{self._base_url}/api/method/erpnext.stock.utils.scan_barcode",
            payload={},
            action_class="query",
            capability_namespace="inventory",
            correlation_id=f"inventory-scan-{uuid4().hex}",
            query_params={"search_value": search_value.strip()},
        )
        if not all(isinstance(value, str) and value.strip() for value in (organization_id, site_id)):
            return transport_error_response(
                request,
                code="SCOPE_MALFORMED",
                message="Inventory scan organization and site scope are required",
                severity="critical",
            )
        if (
            organization_id.strip() != self._expected_organization_id
            or site_id.strip() != self._expected_site_id
        ):
            return transport_error_response(
                request,
                code="SCOPE_MISMATCH",
                message="Inventory scan is outside the configured organization and site scope",
                severity="critical",
            )
        try:
            authorization = self._authorization_header_provider()
        except Exception:
            return transport_error_response(
                request,
                code="AUTH_FAILED",
                message="Connector credentials are unavailable",
                severity="critical",
            )
        if not isinstance(authorization, str) or not authorization.strip():
            return transport_error_response(
                request,
                code="AUTH_FAILED",
                message="Connector credentials are unavailable",
                severity="critical",
            )

        authenticated_request = replace(request, headers={"Authorization": authorization})
        return send_json(authenticated_request, client=self._client, policy=self._policy)