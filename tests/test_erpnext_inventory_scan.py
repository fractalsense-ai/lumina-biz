from __future__ import annotations

import httpx
import pytest

from lumina.business_ops.connectors.erpnext import ERPNextInventoryScanAdapter


@pytest.mark.unit
def test_inventory_scan_calls_permission_checked_erpnext_method() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"message": {"item_code": "ITEM-1", "barcode": "BAR-1", "uom": "Each"}},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test/",
            authorization_header_provider=lambda: "token key:secret",
            client=client,
        )
        result = adapter.lookup(" BAR-1 ")

    assert result.error is None
    assert result.payload == {
        "message": {"item_code": "ITEM-1", "barcode": "BAR-1", "uom": "Each"}
    }
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/api/method/erpnext.stock.utils.scan_barcode"
    assert requests[0].url.params["search_value"] == "BAR-1"
    assert requests[0].headers["Authorization"] == "token key:secret"


@pytest.mark.unit
def test_inventory_scan_returns_empty_result_without_inventing_item() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test",
            authorization_header_provider=lambda: "token key:secret",
            client=client,
        )
        result = adapter.lookup("UNMATCHED")

    assert result.error is None
    assert result.payload == {"message": {}}


@pytest.mark.unit
def test_inventory_scan_normalizes_permission_failure() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"exception": "PermissionError"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test",
            authorization_header_provider=lambda: "token key:secret",
            client=client,
        )
        result = adapter.lookup("BAR-1")

    assert result.error is not None
    assert result.error["code"] == "AUTH_FAILED"
    assert result.error["retryable"] is False


@pytest.mark.unit
@pytest.mark.parametrize("search_value", ["", "  "])
def test_inventory_scan_rejects_empty_search_value(search_value: str) -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda _request: httpx.Response(200))) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test",
            authorization_header_provider=lambda: "token key:secret",
            client=client,
        )

        with pytest.raises(ValueError, match="search_value must be a non-empty string"):
            adapter.lookup(search_value)