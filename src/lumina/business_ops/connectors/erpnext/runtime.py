"""Opt-in ERPNext actor-liveness runtime composition."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os

import httpx

from lumina.business_ops.connectors.transport import TransportPolicy

from .inventory_scan import ERPNextInventoryScanAdapter
from .liveness import ERPNextActorLivenessAdapter

_BASE_URL = "LUMINA_ERP_ACTOR_LIVENESS_BASE_URL"
_ORGANIZATION_ID = "LUMINA_ERP_ACTOR_LIVENESS_ORGANIZATION_ID"
_SITE_ID = "LUMINA_ERP_ACTOR_LIVENESS_SITE_ID"
_API_KEY = "LUMINA_ERP_ACTOR_LIVENESS_API_KEY"
_API_SECRET = "LUMINA_ERP_ACTOR_LIVENESS_API_SECRET"
_REQUIRED_SETTINGS = (_BASE_URL, _ORGANIZATION_ID, _SITE_ID, _API_KEY, _API_SECRET)


@dataclass
class ERPNextActorLivenessRuntime:
    verifier: ERPNextActorLivenessAdapter
    client: httpx.Client
    owns_client: bool

    def close(self) -> None:
        if self.owns_client:
            self.client.close()


@dataclass
class ERPNextInventoryScanRuntime:
    adapter: ERPNextInventoryScanAdapter
    client: httpx.Client
    owns_client: bool

    def close(self) -> None:
        if self.owns_client:
            self.client.close()


def create_erpnext_actor_liveness_runtime(
    *,
    environ: Mapping[str, str] | None = None,
    client: httpx.Client | None = None,
) -> ERPNextActorLivenessRuntime | None:
    """Build the opt-in fixed-scope ERPNext verifier from process configuration."""
    settings = os.environ if environ is None else environ
    values = {name: (settings.get(name) or "").strip() for name in _REQUIRED_SETTINGS}
    if not any(values.values()):
        return None
    if any(not values[name] for name in _REQUIRED_SETTINGS):
        raise ValueError("ERPNext actor-liveness configuration is incomplete")

    owns_client = client is None
    active_client = client or httpx.Client()

    def authorization_header_provider() -> str:
        api_key = (settings.get(_API_KEY) or "").strip()
        api_secret = (settings.get(_API_SECRET) or "").strip()
        if not api_key or not api_secret:
            raise RuntimeError("ERPNext credentials are unavailable")
        return f"token {api_key}:{api_secret}"

    try:
        verifier = ERPNextActorLivenessAdapter(
            base_url=values[_BASE_URL],
            expected_organization_id=values[_ORGANIZATION_ID],
            expected_site_id=values[_SITE_ID],
            authorization_header_provider=authorization_header_provider,
            client=active_client,
            policy=TransportPolicy(),
        )
    except Exception:
        if owns_client:
            active_client.close()
        raise

    return ERPNextActorLivenessRuntime(
        verifier=verifier,
        client=active_client,
        owns_client=owns_client,
    )


def create_erpnext_inventory_scan_runtime(
    *,
    environ: Mapping[str, str] | None = None,
    client: httpx.Client | None = None,
) -> ERPNextInventoryScanRuntime | None:
    """Build the opt-in fixed-scope ERPNext inventory scan adapter."""
    settings = os.environ if environ is None else environ
    values = {name: (settings.get(name) or "").strip() for name in _REQUIRED_SETTINGS}
    if not any(values.values()):
        return None
    if any(not values[name] for name in _REQUIRED_SETTINGS):
        raise ValueError("ERPNext inventory-scan configuration is incomplete")

    owns_client = client is None
    active_client = client or httpx.Client()

    def authorization_header_provider() -> str:
        api_key = (settings.get(_API_KEY) or "").strip()
        api_secret = (settings.get(_API_SECRET) or "").strip()
        if not api_key or not api_secret:
            raise RuntimeError("ERPNext credentials are unavailable")
        return f"token {api_key}:{api_secret}"

    try:
        adapter = ERPNextInventoryScanAdapter(
            base_url=values[_BASE_URL],
            expected_organization_id=values[_ORGANIZATION_ID],
            expected_site_id=values[_SITE_ID],
            authorization_header_provider=authorization_header_provider,
            client=active_client,
            policy=TransportPolicy(),
        )
    except Exception:
        if owns_client:
            active_client.close()
        raise

    return ERPNextInventoryScanRuntime(
        adapter=adapter,
        client=active_client,
        owns_client=owns_client,
    )