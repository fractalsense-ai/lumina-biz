from __future__ import annotations

import pytest

from lumina.business_ops.connectors.erpnext import DeterministicFixtureRunner, FixtureScenario


@pytest.mark.unit
def test_fixture_runner_returns_matching_scenario_payload() -> None:
    runner = DeterministicFixtureRunner(
        [
            FixtureScenario(
                scenario_id="wo-query-ok",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "service/work-order",
                },
                result_payload={
                    "status": "succeeded",
                    "data": {"records": [{"name": "WO-0001"}]},
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
    assert result["data"]["records"][0]["name"] == "WO-0001"  # type: ignore[index]


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
