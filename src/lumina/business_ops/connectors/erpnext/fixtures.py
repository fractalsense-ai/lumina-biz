"""Deterministic fixture execution helpers for ERPNext connector tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FixtureScenario:
    scenario_id: str
    request_match: dict[str, str]
    result_payload: dict[str, object]


class DeterministicFixtureRunner:
    """Pure fixture runner for provider-independent CI/test execution."""

    def __init__(self, scenarios: list[FixtureScenario]):
        self._scenarios = list(scenarios)

    def run(self, request: dict[str, object]) -> dict[str, object]:
        action_class = str(request.get("action_class") or "").strip()
        capability_namespace = str(request.get("capability_namespace") or "").strip()

        for scenario in self._scenarios:
            if scenario.request_match.get("action_class") != action_class:
                continue
            if scenario.request_match.get("capability_namespace") != capability_namespace:
                continue
            return dict(scenario.result_payload)

        return {
            "status": "failed",
            "errors": [
                {
                    "code": "FIXTURE_NOT_FOUND",
                    "message": "No deterministic fixture scenario matched the request",
                    "severity": "error",
                    "retryable": False,
                    "action_class": action_class,
                    "capability_namespace": capability_namespace,
                }
            ],
        }
