from __future__ import annotations

import httpx
import pytest

from lumina.business_ops.connectors.erpnext import ERPNextInventoryScanAdapter

_ORG_ID = "org-1"
_SITE_ID = "site-1"


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
            expected_organization_id=_ORG_ID,
            expected_site_id=_SITE_ID,
            authorization_header_provider=lambda: "token key:secret",
            client=client,
        )
        result = adapter.lookup(" BAR-1 ", organization_id=_ORG_ID, site_id=_SITE_ID)

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
            expected_organization_id=_ORG_ID,
            expected_site_id=_SITE_ID,
            authorization_header_provider=lambda: "token key:secret",
            client=client,
        )
        result = adapter.lookup("UNMATCHED", organization_id=_ORG_ID, site_id=_SITE_ID)

    assert result.error is None
    assert result.payload == {"message": {}}


@pytest.mark.unit
def test_inventory_scan_normalizes_permission_failure() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"exception": "PermissionError"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test",
            expected_organization_id=_ORG_ID,
            expected_site_id=_SITE_ID,
            authorization_header_provider=lambda: "token key:secret",
            client=client,
        )
        result = adapter.lookup("BAR-1", organization_id=_ORG_ID, site_id=_SITE_ID)

    assert result.error is not None
    assert result.error["code"] == "AUTH_FAILED"
    assert result.error["retryable"] is False


@pytest.mark.unit
def test_inventory_scan_normalizes_credential_provider_exception_without_leaking_details() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    def unavailable_credentials() -> str:
        raise RuntimeError("secret provider diagnostics")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test",
            expected_organization_id=_ORG_ID,
            expected_site_id=_SITE_ID,
            authorization_header_provider=unavailable_credentials,
            client=client,
        )
        result = adapter.lookup("BAR-1", organization_id=_ORG_ID, site_id=_SITE_ID)

    assert result.error is not None
    assert result.error["code"] == "AUTH_FAILED"
    assert result.error["message"] == "Connector credentials are unavailable"
    assert result.error["details"]["attempts"] == 0  # type: ignore[index]
    assert "secret provider diagnostics" not in repr(result.error)
    assert requests == []


@pytest.mark.unit
def test_inventory_scan_normalizes_empty_authorization_header() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test",
            expected_organization_id=_ORG_ID,
            expected_site_id=_SITE_ID,
            authorization_header_provider=lambda: "  ",
            client=client,
        )
        result = adapter.lookup("BAR-1", organization_id=_ORG_ID, site_id=_SITE_ID)

    assert result.error is not None
    assert result.error["code"] == "AUTH_FAILED"
    assert result.error["message"] == "Connector credentials are unavailable"
    assert result.error["details"]["attempts"] == 0  # type: ignore[index]
    assert requests == []


@pytest.mark.unit
@pytest.mark.parametrize("search_value", ["", "  "])
def test_inventory_scan_rejects_empty_search_value(search_value: str) -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda _request: httpx.Response(200))) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test",
            expected_organization_id=_ORG_ID,
            expected_site_id=_SITE_ID,
            authorization_header_provider=lambda: "token key:secret",
            client=client,
        )

        with pytest.raises(ValueError, match="search_value must be a non-empty string"):
            adapter.lookup(search_value, organization_id=_ORG_ID, site_id=_SITE_ID)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("organization_id", "site_id", "error_code"),
    [
        ("org-2", "site-1", "SCOPE_MISMATCH"),
        ("org-1", "site-2", "SCOPE_MISMATCH"),
        ("", "site-1", "SCOPE_MALFORMED"),
    ],
)
def test_inventory_scan_rejects_scope_before_http(
    organization_id: str,
    site_id: str,
    error_code: str,
) -> None:
    requests: list[httpx.Request] = []
    credential_provider_calls = 0

    def provide_credentials() -> str:
        nonlocal credential_provider_calls
        credential_provider_calls += 1
        return "token key:secret"

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        adapter = ERPNextInventoryScanAdapter(
            base_url="https://erp.example.test",
            expected_organization_id=_ORG_ID,
            expected_site_id=_SITE_ID,
            authorization_header_provider=provide_credentials,
            client=client,
        )
        result = adapter.lookup(
            "BAR-1",
            organization_id=organization_id,
            site_id=site_id,
        )

    assert result.error is not None
    assert result.error["code"] == error_code
    assert result.error["retryable"] is False
    assert result.error["details"]["attempts"] == 0  # type: ignore[index]
    assert credential_provider_calls == 0
    assert requests == []