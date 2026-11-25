from __future__ import annotations

import pytest

from lumina.business_ops.connectors.erpnext import (
    build_connector_manifest,
    map_operation_to_erpnext,
    normalize_erpnext_error,
)


@pytest.mark.unit
def test_manifest_declares_provider_and_capabilities() -> None:
    manifest = build_connector_manifest()

    assert manifest["connector_id"] == "connector.erpnext.v1"
    assert manifest["provider_family"] == "erpnext"
    assert manifest["authentication"]["mode"] == "runtime_secret"  # type: ignore[index]

    caps = {c["namespace"]: tuple(c["supported_actions"]) for c in manifest["capabilities"]}  # type: ignore[index]
    assert "service/work-order" in caps
    assert caps.get("inventory") == ("query", "create_draft", "update_draft")
    assert caps.get("sales/pos") == ("query",)
    assert "warehouse/storage" in caps
    assert "logistics/dispatch" in caps
    assert "scheduling" in caps


@pytest.mark.unit
def test_mapping_query_work_order() -> None:
    payload = map_operation_to_erpnext(
        {
            "action_class": "query",
            "capability_namespace": "service/work-order",
            "payload": {"filters": {"name": ["like", "WO-%"]}, "limit": 25},
        }
    )
    assert payload["doctype"] == "Work Order"
    assert payload["operation"] == "get_list"
    assert payload["limit"] == 25


@pytest.mark.unit
def test_mapping_query_pos_invoices() -> None:
    payload = map_operation_to_erpnext(
        {
            "action_class": "query",
            "capability_namespace": "sales/pos",
            "payload": {
                "filters": {"docstatus": 1},
                "fields": ["name", "posting_date", "grand_total"],
                "limit": 20,
                "order_by": "posting_date desc",
            },
        }
    )

    assert payload["doctype"] == "POS Invoice"
    assert payload["operation"] == "get_list"
    assert payload["filters"] == {"docstatus": 1}
    assert payload["fields"] == ["name", "posting_date", "grand_total"]
    assert payload["limit"] == 20
    assert payload["order_by"] == "posting_date desc"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("operation_kind", "doctype"),
    [("receiving", "Stock Entry"), ("count", "Stock Reconciliation")],
)
def test_mapping_inventory_create_draft(operation_kind: str, doctype: str) -> None:
    payload = map_operation_to_erpnext(
        {
            "action_class": "create_draft",
            "capability_namespace": "inventory",
            "payload": {
                "operation_kind": operation_kind,
                "record": {"items": [{"item_code": "ITEM-1", "qty": 2}]},
            },
        }
    )
    assert payload["doctype"] == doctype
    assert payload["operation"] == "insert"
    assert payload["submit"] is False


@pytest.mark.unit
def test_mapping_inventory_update_draft_requires_record_envelope() -> None:
    payload = map_operation_to_erpnext(
        {
            "action_class": "update_draft",
            "capability_namespace": "service/work-order",
            "payload": {
                "record_id": "WO-0001",
                "record": {"status": "Open"},
            },
        }
    )
    assert payload["operation"] == "update"
    assert payload["name"] == "WO-0001"


@pytest.mark.unit
def test_mapping_inventory_update_draft_keeps_stock_document_unsubmitted() -> None:
    payload = map_operation_to_erpnext(
        {
            "action_class": "update_draft",
            "capability_namespace": "inventory",
            "payload": {
                "operation_kind": "receiving",
                "record_id": "STE-0001",
                "record": {"items": [{"item_code": "ITEM-1", "qty": 3}]},
            },
        }
    )
    assert payload["doctype"] == "Stock Entry"
    assert payload["operation"] == "update"
    assert payload["name"] == "STE-0001"


@pytest.mark.unit
def test_mapping_inventory_request_commit_remains_unsupported() -> None:
    with pytest.raises(ValueError):
        map_operation_to_erpnext(
            {
                "action_class": "request_commit",
                "capability_namespace": "inventory",
                "payload": {"record_id": "STE-0001"},
            }
        )


@pytest.mark.unit
def test_mapping_unsupported_pair_raises() -> None:
    with pytest.raises(ValueError):
        map_operation_to_erpnext(
            {
                "action_class": "request_cancel",
                "capability_namespace": "inventory",
                "payload": {},
            }
        )


@pytest.mark.unit
def test_mapping_rejects_unexpected_query_payload_keys() -> None:
    with pytest.raises(ValueError):
        map_operation_to_erpnext(
            {
                "action_class": "query",
                "capability_namespace": "inventory",
                "payload": {"vertical_specific": "tow-truck"},
            }
        )


@pytest.mark.unit
def test_error_normalization_for_rate_limit() -> None:
    err = normalize_erpnext_error(
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
