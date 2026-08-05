from __future__ import annotations

import pytest

from lumina.business_ops.connectors.odoo import (
    build_connector_manifest,
    map_operation_to_odoo,
    normalize_odoo_error,
)


@pytest.mark.unit
def test_manifest_declares_provider_and_capabilities() -> None:
    manifest = build_connector_manifest()

    assert manifest["connector_id"] == "connector.odoo.v1"
    assert manifest["provider_family"] == "odoo"
    assert manifest["authentication"]["mode"] == "runtime_secret"  # type: ignore[index]

    caps = {c["namespace"]: tuple(c["supported_actions"]) for c in manifest["capabilities"]}  # type: ignore[index]
    assert "service/work-order" in caps
    assert "inventory" in caps
    assert "warehouse/storage" in caps
    assert "logistics/dispatch" in caps
    assert "scheduling" in caps


@pytest.mark.unit
def test_mapping_query_work_order() -> None:
    payload = map_operation_to_odoo(
        {
            "action_class": "query",
            "capability_namespace": "service/work-order",
            "payload": {"filters": {"name": ["like", "WO-%"]}, "limit": 25},
        }
    )
    assert payload["model"] == "helpdesk.ticket"
    assert payload["operation"] == "search_read"
    assert payload["limit"] == 25


@pytest.mark.unit
def test_mapping_update_draft_requires_record_envelope() -> None:
    payload = map_operation_to_odoo(
        {
            "action_class": "update_draft",
            "capability_namespace": "service/work-order",
            "payload": {
                "record_id": "TICKET-0001",
                "record": {"stage": "open"},
            },
        }
    )
    assert payload["operation"] == "write"
    assert payload["id"] == "TICKET-0001"


@pytest.mark.unit
def test_mapping_unsupported_pair_raises() -> None:
    with pytest.raises(ValueError):
        map_operation_to_odoo(
            {
                "action_class": "request_cancel",
                "capability_namespace": "inventory",
                "payload": {},
            }
        )


@pytest.mark.unit
def test_mapping_rejects_unexpected_query_payload_keys() -> None:
    with pytest.raises(ValueError):
        map_operation_to_odoo(
            {
                "action_class": "query",
                "capability_namespace": "inventory",
                "payload": {"vertical_specific": "tow-truck"},
            }
        )


@pytest.mark.unit
def test_error_normalization_for_rate_limit() -> None:
    err = normalize_odoo_error(
        status_code=429,
        message="Too many requests",
        action_class="query",
        capability_namespace="inventory",
        provider_error_code="RATE_LIMIT",
        provider_message="Burst threshold exceeded",
        details={"retry_after_seconds": 5},
    )
    assert err["code"] == "RATE_LIMITED"
    assert err["retryable"] is True
    assert err["action_class"] == "query"
    assert err["provider_error_code"] == "RATE_LIMIT"
