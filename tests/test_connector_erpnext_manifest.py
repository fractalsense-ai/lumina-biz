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
    assert "inventory" in caps


@pytest.mark.unit
def test_mapping_query_work_order() -> None:
    payload = map_operation_to_erpnext(
        {
            "action_class": "query",
            "capability_namespace": "service/work-order",
            "payload": {"name": ["like", "WO-%"]},
        }
    )
    assert payload["doctype"] == "Work Order"
    assert payload["operation"] == "get_list"


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
def test_error_normalization_for_rate_limit() -> None:
    err = normalize_erpnext_error(
        status_code=429,
        message="Too many requests",
        action_class="query",
        capability_namespace="inventory",
    )
    assert err["code"] == "RATE_LIMITED"
    assert err["retryable"] is True
    assert err["action_class"] == "query"
