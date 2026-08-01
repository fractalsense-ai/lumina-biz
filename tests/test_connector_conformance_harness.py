from __future__ import annotations

import pytest

from lumina.business_ops.connectors import conformance
from lumina.business_ops.connectors import erpnext, odoo


def _request(*, request_id: str, action_class: str, capability_namespace: str, payload: dict[str, object]) -> dict[str, object]:
    return {
        "request_id": request_id,
        "action_class": action_class,
        "capability_namespace": capability_namespace,
        "payload": payload,
        "actor_scope": {
            "organization_id": "org-a",
            "site_id": "site-a",
            "actor_id": "actor-a",
        },
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    "provider_module,provider_family",
    [(erpnext, "erpnext"), (odoo, "odoo")],
)
def test_conformance_suite_runs_shared_scenarios(provider_module, provider_family: str) -> None:
    scenarios = [
        conformance.ConformanceScenario(
            scenario_id="query-work-order-ok",
            request=_request(
                request_id="req-query-1",
                action_class="query",
                capability_namespace="service/work-order",
                payload={"filters": {"status": ["=", "Open"]}},
            ),
            fixture_result={"status": "succeeded", "data": {"records": [{"id": "WO-1"}]}} ,
            expected_status="completed",
        ),
        conformance.ConformanceScenario(
            scenario_id="unsupported-op-fails",
            request=_request(
                request_id="req-unsupported-1",
                action_class="request_cancel",
                capability_namespace="inventory",
                payload={},
            ),
            expected_status="failed",
            expected_error_code="UNSUPPORTED_MAPPING",
        ),
    ]

    results = conformance.run_conformance_suite(
        provider_module,
        scenarios,
        expected_scope={"organization_id": "org-a", "site_id": "site-a"},
    )

    assert len(results) == 2
    assert all(result.provider == provider_family for result in results)
    assert all(result.passed for result in results)
    assert [result.scenario_id for result in results] == ["query-work-order-ok", "unsupported-op-fails"]


@pytest.mark.unit
def test_conformance_suite_emits_failure_summary_on_mismatch() -> None:
    scenarios = [
        conformance.ConformanceScenario(
            scenario_id="bad-expectation",
            request=_request(
                request_id="req-bad-1",
                action_class="query",
                capability_namespace="inventory",
                payload={"filters": {"item_code": ["=", "SKU-1"]}},
            ),
            fixture_result={"status": "succeeded", "data": {"records": []}},
            expected_status="failed",
        )
    ]

    results = conformance.run_conformance_suite(erpnext, scenarios)
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].error_summary is not None
