from __future__ import annotations

import pytest

from lumina.business_ops.connectors.odoo import (
    DeterministicFixtureRunner,
    FixtureScenario,
    execute_with_fixtures,
)


@pytest.mark.unit
def test_fixture_runner_returns_matching_scenario_payload() -> None:
    runner = DeterministicFixtureRunner(
        [
            FixtureScenario(
                scenario_id="odoo-query-ok",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "service/work-order",
                },
                result_payload={
                    "status": "succeeded",
                    "data": {"records": [{"name": "TICKET-0001"}]},
                },
            )
        ]
    )

    result = runner.run(
        {
            "action_class": "query",
            "capability_namespace": "service/work-order",
        }
    )

    assert result["status"] == "succeeded"
    assert result["data"]["records"][0]["name"] == "TICKET-0001"  # type: ignore[index]


@pytest.mark.unit
def test_fixture_runner_returns_structured_error_on_miss() -> None:
    runner = DeterministicFixtureRunner([])
    result = runner.run(
        {
            "action_class": "query",
            "capability_namespace": "inventory",
        }
    )

    assert result["status"] == "failed"
    errors = result.get("errors")
    assert isinstance(errors, list)
    assert errors[0]["code"] == "FIXTURE_NOT_FOUND"


@pytest.mark.unit
def test_execute_rejects_cross_tenant_scope_mismatch() -> None:
    runner = DeterministicFixtureRunner([])
    result = execute_with_fixtures(
        {
            "request_id": "req-odoo-scope-mismatch",
            "action_class": "query",
            "capability_namespace": "inventory",
            "payload": {},
            "actor_scope": {
                "organization_id": "org-b",
                "site_id": "site-a",
                "actor_id": "u-2",
            },
        },
        runner,
        expected_scope={
            "organization_id": "org-a",
            "site_id": "site-a",
        },
    )
    assert result["status"] == "failed"
    errors = result.get("errors")
    assert isinstance(errors, list)
    assert errors[0]["code"] == "SCOPE_MISMATCH"
