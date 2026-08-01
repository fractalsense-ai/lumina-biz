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
        scope = request.get("actor_scope") if isinstance(request.get("actor_scope"), dict) else {}
        organization_id = str(scope.get("organization_id") or "").strip()
        site_id = str(scope.get("site_id") or "").strip()
        actor_id = str(scope.get("actor_id") or "").strip()

        best_match: FixtureScenario | None = None
        best_specificity = -1

        for scenario in self._scenarios:
            if scenario.request_match.get("action_class") != action_class:
                continue
            if scenario.request_match.get("capability_namespace") != capability_namespace:
                continue
            if scenario.request_match.get("organization_id") and scenario.request_match.get("organization_id") != organization_id:
                continue
            if scenario.request_match.get("site_id") and scenario.request_match.get("site_id") != site_id:
                continue
            if scenario.request_match.get("actor_id") and scenario.request_match.get("actor_id") != actor_id:
                continue

            specificity = len(scenario.request_match)
            if specificity > best_specificity:
                best_match = scenario
                best_specificity = specificity

        if best_match is not None:
            return dict(best_match.result_payload)

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
