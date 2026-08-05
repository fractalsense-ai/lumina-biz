"""Provider-agnostic connector conformance harness for Slice 34."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ConformanceScenario:
    scenario_id: str
    request: dict[str, object]
    fixture_result: dict[str, object] | None = None
    expected_status: str = "completed"
    expected_error_code: str | None = None


@dataclass(frozen=True)
class ConnectorConformanceResult:
    provider: str
    scenario_id: str
    capability_namespace: str
    action_class: str
    passed: bool
    error_summary: str | None = None

    def as_record(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "scenario_id": self.scenario_id,
            "capability_namespace": self.capability_namespace,
            "action_class": self.action_class,
            "passed": self.passed,
            "error_summary": self.error_summary,
        }


class _FixtureScenarioFactory(Protocol):
    def __call__(self, scenario_id: str, request_match: dict[str, str], result_payload: dict[str, object]) -> Any:
        ...


class _RunnerFactory(Protocol):
    def __call__(self, scenarios: list[Any]) -> Any:
        ...


class ConnectorProviderModule(Protocol):
    FixtureScenario: _FixtureScenarioFactory
    DeterministicFixtureRunner: _RunnerFactory

    def build_connector_manifest(self) -> dict[str, object]:
        ...

    def execute_with_fixtures(
        self,
        request: dict[str, object],
        fixture_runner: Any,
        *,
        expected_scope: dict[str, str] | None = None,
    ) -> dict[str, object]:
        ...


def _to_fixture_scenario(provider_module: ConnectorProviderModule, scenario: ConformanceScenario) -> Any:
    request = scenario.request
    return provider_module.FixtureScenario(
        scenario_id=scenario.scenario_id,
        request_match={
            "action_class": str(request.get("action_class") or "").strip(),
            "capability_namespace": str(request.get("capability_namespace") or "").strip(),
            "organization_id": str(((request.get("actor_scope") or {}) if isinstance(request.get("actor_scope"), dict) else {}).get("organization_id") or "").strip(),
            "site_id": str(((request.get("actor_scope") or {}) if isinstance(request.get("actor_scope"), dict) else {}).get("site_id") or "").strip(),
        },
        result_payload=scenario.fixture_result or {"status": "succeeded", "data": {}},
    )


def run_conformance_suite(
    provider_module: ConnectorProviderModule,
    scenarios: list[ConformanceScenario],
    *,
    expected_scope: dict[str, str] | None = None,
) -> list[ConnectorConformanceResult]:
    """Run canonical conformance scenarios against a connector module."""
    provider = str(provider_module.build_connector_manifest().get("provider_family") or "unknown")
    fixture_scenarios = [_to_fixture_scenario(provider_module, scenario) for scenario in scenarios]
    runner = provider_module.DeterministicFixtureRunner(fixture_scenarios)

    results: list[ConnectorConformanceResult] = []
    for scenario in scenarios:
        execution = provider_module.execute_with_fixtures(
            dict(scenario.request),
            runner,
            expected_scope=expected_scope,
        )
        capability_namespace = str(scenario.request.get("capability_namespace") or "").strip()
        action_class = str(scenario.request.get("action_class") or "").strip()

        status = str(execution.get("status") or "").strip().lower()
        passed = status == scenario.expected_status
        error_summary: str | None = None

        if scenario.expected_error_code is not None:
            errors = execution.get("errors")
            first_code = None
            if isinstance(errors, list) and errors and isinstance(errors[0], dict):
                first_code = str(errors[0].get("code") or "").strip()
            if first_code != scenario.expected_error_code:
                passed = False
                error_summary = (
                    f"expected error code {scenario.expected_error_code!r}, got {first_code!r}"
                )

        if not passed and error_summary is None:
            error_summary = f"expected status {scenario.expected_status!r}, got {status!r}"

        results.append(
            ConnectorConformanceResult(
                provider=provider,
                scenario_id=scenario.scenario_id,
                capability_namespace=capability_namespace,
                action_class=action_class,
                passed=passed,
                error_summary=error_summary,
            )
        )

    return results
