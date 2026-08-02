from __future__ import annotations

import pytest

from lumina.business_ops.connectors.erpnext import (
    DeterministicFixtureRunner,
    FixtureScenario,
    execute_with_fixtures,
)


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


@pytest.mark.unit
def test_fixture_runner_can_match_with_tenant_scope() -> None:
    runner = DeterministicFixtureRunner(
        [
            FixtureScenario(
                scenario_id="wo-query-org-site",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "service/work-order",
                    "organization_id": "org-a",
                    "site_id": "site-a",
                },
                result_payload={"status": "succeeded", "data": {"records": [{"name": "WO-0002"}]}},
            )
        ]
    )
    result = runner.run(
        {
            "action_class": "query",
            "capability_namespace": "service/work-order",
            "actor_scope": {
                "organization_id": "org-a",
                "site_id": "site-a",
                "actor_id": "u-1",
            },
        }
    )
    assert result["status"] == "succeeded"


@pytest.mark.unit
def test_execute_rejects_missing_actor_scope() -> None:
    runner = DeterministicFixtureRunner([])
    result = execute_with_fixtures(
        {
            "request_id": "req-missing-scope",
            "action_class": "query",
            "capability_namespace": "inventory",
            "payload": {},
        },
        runner,
    )
    assert result["status"] == "failed"
    errors = result.get("errors")
    assert isinstance(errors, list)
    assert errors[0]["code"] == "MISSING_ACTOR_SCOPE"


@pytest.mark.unit
def test_execute_rejects_cross_tenant_scope_mismatch() -> None:
    runner = DeterministicFixtureRunner([])
    result = execute_with_fixtures(
        {
            "request_id": "req-scope-mismatch",
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


@pytest.mark.unit
@pytest.mark.parametrize(
    "status_code,expected_code",
    [
        (400, "VALIDATION_FAILED"),
        (401, "AUTH_FAILED"),
        (429, "RATE_LIMITED"),
        (503, "UPSTREAM_UNAVAILABLE"),
    ],
)
def test_execute_normalizes_provider_failure_codes(status_code: int, expected_code: str) -> None:
    runner = DeterministicFixtureRunner(
        [
            FixtureScenario(
                scenario_id=f"err-{status_code}",
                request_match={
                    "action_class": "query",
                    "capability_namespace": "inventory",
                    "organization_id": "org-a",
                    "site_id": "site-a",
                },
                result_payload={
                    "status": "failed",
                    "errors": [
                        {
                            "status_code": status_code,
                            "provider_error_code": f"E{status_code}",
                            "provider_message": "Provider failed",
                            "message": "Fixture provider failure",
                            "details": {"path": "/api/resource"},
                        }
                    ],
                },
            )
        ]
    )

    result = execute_with_fixtures(
        {
            "request_id": f"req-{status_code}",
            "action_class": "query",
            "capability_namespace": "inventory",
            "payload": {"filters": {"item_code": ["=", "SKU-1"]}},
            "actor_scope": {
                "organization_id": "org-a",
                "site_id": "site-a",
                "actor_id": "u-3",
            },
        },
        runner,
        expected_scope={"organization_id": "org-a", "site_id": "site-a"},
    )

    assert result["status"] == "failed"
    errors = result.get("errors")
    assert isinstance(errors, list)
    assert errors[0]["code"] == expected_code
    assert errors[0]["provider_error_code"] == f"E{status_code}"
