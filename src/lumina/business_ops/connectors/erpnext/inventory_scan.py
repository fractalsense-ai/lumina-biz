"""Permission-checked ERPNext inventory scan lookup adapter."""

from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

import httpx

from lumina.business_ops.connectors.transport import (
    ConnectorTransportRequest,
    ConnectorTransportResponse,
    TransportPolicy,
    send_json,
)


class ERPNextInventoryScanAdapter:
    """Resolve barcode, serial, batch, or warehouse scans through ERPNext."""

    def __init__(
        self,
        *,
        base_url: str,
        authorization_header_provider: Callable[[], str],
        client: httpx.Client,
        policy: TransportPolicy = TransportPolicy(),
    ) -> None:
        normalized_base_url = base_url.strip().rstrip("/")
        if not normalized_base_url.startswith(("http://", "https://")):
            raise ValueError("ERPNext base_url must use HTTP or HTTPS")
        if not callable(authorization_header_provider):
            raise ValueError("authorization_header_provider must be callable")
        self._base_url = normalized_base_url
        self._authorization_header_provider = authorization_header_provider
        self._client = client
        self._policy = policy

    def lookup(self, search_value: str) -> ConnectorTransportResponse:
        """Call ERPNext's permission-checked scan method without mutating stock."""
        if not isinstance(search_value, str) or not search_value.strip():
            raise ValueError("search_value must be a non-empty string")
        authorization = self._authorization_header_provider()
        if not isinstance(authorization, str) or not authorization.strip():
            raise ValueError("ERPNext authorization header is unavailable")

        request = ConnectorTransportRequest(
            method="GET",
            url=f"{self._base_url}/api/method/erpnext.stock.utils.scan_barcode",
            payload={},
            action_class="query",
            capability_namespace="inventory",
            correlation_id=f"inventory-scan-{uuid4().hex}",
            headers={"Authorization": authorization},
            query_params={"search_value": search_value.strip()},
        )
        return send_json(request, client=self._client, policy=self._policy)