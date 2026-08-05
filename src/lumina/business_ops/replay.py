"""Deterministic Business Ops fixture replay for CI evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from lumina.connector_routing.router import (
    CapabilityRoute,
    CapabilityRoutePolicy,
    ConnectorRegistryEntry,
    resolve_connector,
)
from lumina.decision_precedent.policy import resolve_decision_precedent_policy
from lumina.decision_precedent.scorer import PrecedentCandidate, score_decision_precedent
from lumina.thread_routing.policy import resolve_thread_routing_policy
from lumina.thread_routing.router import ThreadCandidate, decide_thread_route


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(UTC)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping YAML at {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object JSON at {path}")
    return data


def _resolve_connector_fixture(
    connector_fixture: dict[str, Any],
    *,
    scope: dict[str, Any],
) -> dict[str, Any]:
    connector_entries = [
        ConnectorRegistryEntry(
            organization_id=item["organization_id"],
            site_id=item["site_id"],
            connector_instance_id=item["connector_instance_id"],
            capability_namespaces=tuple(item["capability_namespaces"]),
            supported_action_classes=tuple(item["supported_action_classes"]),
            enabled=bool(item["enabled"]),
            health_status=item["health_status"],
            is_site_primary=bool(item.get("is_site_primary", False)),
        )
        for item in connector_fixture["entries"]
    ]
    routes = [
        CapabilityRoute(
            capability_namespace=item["capability_namespace"],
            connector_instance_id=item["connector_instance_id"],
            supported_action_classes=tuple(item.get("supported_action_classes") or ()),
            priority=int(item.get("priority", 100)),
        )
        for item in connector_fixture["routes"]
    ]
    connector_policy = CapabilityRoutePolicy(
        policy_version=1,
        organization_id=scope["organization_id"],
        site_id=scope["site_id"],
        routes=tuple(routes),
        organization_default_connector_id=None,
    )
    connector_resolution = resolve_connector(
        connector_entries,
        connector_policy,
        request_id=connector_fixture["request_id"],
        actor_id=scope["actor_id"],
        action_class=connector_fixture["action_class"],
        capability_namespace=connector_fixture["capability_namespace"],
        idempotency_key=connector_fixture.get("idempotency_key"),
        correlation_id=connector_fixture.get("correlation_id"),
    )
    expected = connector_fixture["expected"]
    return {
        "record": connector_resolution.as_record(),
        "expected": expected,
        "matches_expected": {
            "status": connector_resolution.status == expected["status"],
            "source": connector_resolution.source == expected["source"],
            "reason_code": connector_resolution.reason_code == expected["reason_code"],
            "connector_instance_id": (
                connector_resolution.connector_instance_id
                == expected["connector_instance_id"]
            ),
        },
    }


def _evaluate_connector_portability(
    portability_cfg: dict[str, Any] | None,
    *,
    scope: dict[str, Any],
) -> dict[str, Any] | None:
    if not portability_cfg:
        return None

    def _evaluate_scenario(
        scenario_id: str,
        providers: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        evaluated: list[dict[str, Any]] = []
        canonical_signatures: list[Any] = []
        for item in providers:
            if not isinstance(item, dict):
                continue
            provider = str(item.get("provider") or "unknown")
            step_fixtures = item.get("connector_resolution_steps")
            step_reports: list[dict[str, Any]] = []
            step_signatures: list[dict[str, str]] = []

            if isinstance(step_fixtures, list) and step_fixtures:
                for raw_step in step_fixtures:
                    if not isinstance(raw_step, dict):
                        continue
                    report = _resolve_connector_fixture(raw_step, scope=scope)
                    rec = report["record"]
                    step_reports.append(report)
                    step_signatures.append(
                        {
                            "status": rec["status"],
                            "source": rec["source"],
                            "reason_code": rec["reason_code"],
                        }
                    )
                if not step_reports:
                    continue
                signature: Any = step_signatures
            else:
                fixture = item.get("connector_resolution")
                if not isinstance(fixture, dict):
                    continue
                report = _resolve_connector_fixture(fixture, scope=scope)
                rec = report["record"]
                step_reports = [report]
                signature = {
                    "status": rec["status"],
                    "source": rec["source"],
                    "reason_code": rec["reason_code"],
                }

            canonical_expected = item.get("canonical_expected")
            if isinstance(canonical_expected, dict):
                signature_match = all(
                    signature.get(k) == canonical_expected.get(k)
                    for k in ("status", "source", "reason_code")
                    if k in canonical_expected
                )
            elif isinstance(canonical_expected, list) and isinstance(signature, list):
                signature_match = len(signature) == len(canonical_expected) and all(
                    isinstance(sig_item, dict)
                    and isinstance(exp_item, dict)
                    and all(
                        sig_item.get(k) == exp_item.get(k)
                        for k in ("status", "source", "reason_code")
                        if k in exp_item
                    )
                    for sig_item, exp_item in zip(signature, canonical_expected)
                )
            else:
                signature_match = True
            canonical_signatures.append(signature)
            evaluated.append(
                {
                    "provider": provider,
                    "connector_resolution": step_reports[0],
                    "connector_resolution_steps": step_reports,
                    "canonical_signature": signature,
                    "matches_canonical_expected": signature_match,
                }
            )

        if not evaluated:
            return None
        baseline = canonical_signatures[0]
        parity_matches = [sig == baseline for sig in canonical_signatures]
        return {
            "scenario_id": scenario_id,
            "providers": evaluated,
            "canonical_baseline": baseline,
            "parity_matches": parity_matches,
            "all_match": all(parity_matches),
            "all_match_expected": all(p["matches_canonical_expected"] for p in evaluated),
        }

    matrix_cfg = portability_cfg.get("scenario_matrix")
    if isinstance(matrix_cfg, list) and matrix_cfg:
        scenario_reports: list[dict[str, Any]] = []
        for idx, raw_scenario in enumerate(matrix_cfg, start=1):
            if not isinstance(raw_scenario, dict):
                continue
            scenario_id = str(raw_scenario.get("scenario_id") or f"scenario_{idx}")
            providers = raw_scenario.get("providers")
            if not isinstance(providers, list) or not providers:
                continue
            scenario_report = _evaluate_scenario(scenario_id, providers)
            if scenario_report is not None:
                scenario_reports.append(scenario_report)
        if not scenario_reports:
            return None
        return {
            "mode": "scenario_matrix",
            "scenarios": scenario_reports,
            "all_match": all(s["all_match"] for s in scenario_reports),
            "all_match_expected": all(s["all_match_expected"] for s in scenario_reports),
        }

    scenarios = portability_cfg.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        return None
    return _evaluate_scenario(
        str(portability_cfg.get("scenario_id") or "connector_portability"),
        scenarios,
    )


def generate_replay_report(
    fixture_path: str | Path,
    *,
    thread_policy_path: str | Path,
    decision_policy_path: str | Path,
) -> dict[str, Any]:
    """Replay business-ops fixture and return deterministic evidence payload."""
    fixture = _load_json(Path(fixture_path))
    scope = fixture["scope"]

    thread_policy = resolve_thread_routing_policy(
        _load_yaml(Path(thread_policy_path)),
        organization_id=scope["organization_id"],
        site_id=scope["site_id"],
    )
    thread_candidates = [ThreadCandidate(**item) for item in fixture["thread_routing"]["candidates"]]
    thread_decision = decide_thread_route(
        thread_candidates,
        thread_policy,
        actor_id=scope["actor_id"],
        decision_id=fixture["thread_routing"]["decision_id"],
        new_thread_id=fixture["thread_routing"]["new_thread_id"],
    )

    precedent_policy = resolve_decision_precedent_policy(
        _load_yaml(Path(decision_policy_path)),
        organization_id=scope["organization_id"],
        site_id=scope["site_id"],
    )
    precedent_candidates = [
        PrecedentCandidate(
            summary_record_id=item["summary_record_id"],
            thread_id=item["thread_id"],
            similarity=float(item["similarity"]),
            created_utc=_parse_utc(item["created_utc"]),
        )
        for item in fixture["decision_precedent"]["candidates"]
    ]
    precedent_score = score_decision_precedent(
        precedent_candidates,
        precedent_policy,
        actor_id=scope["actor_id"],
        risk_class=fixture["decision_precedent"]["risk_class"],
        evaluated_utc=_parse_utc(fixture["decision_precedent"]["evaluated_utc"]),
        record_id=fixture["decision_precedent"]["record_id"],
    )

    connector_fixture = fixture["connector_resolution"]
    connector_report = _resolve_connector_fixture(connector_fixture, scope=scope)
    portability_report = _evaluate_connector_portability(
        fixture.get("connector_portability"),
        scope=scope,
    )

    result = {
        "schema_version": "1.0.0",
        "fixture_id": fixture["fixture_id"],
        "scope": dict(scope),
        "thread_routing": {
            "record": thread_decision.as_record(created_utc=_parse_utc("2026-07-30T12:00:00Z")),
            "expected": fixture["thread_routing"]["expected"],
            "matches_expected": {
                "decision": thread_decision.decision == fixture["thread_routing"]["expected"]["decision"],
                "thread_id": thread_decision.thread_id == fixture["thread_routing"]["expected"]["thread_id"],
                "rationale_code": thread_decision.rationale_code == fixture["thread_routing"]["expected"]["rationale_code"],
                "operator_confirmation_required": (
                    thread_decision.operator_confirmation_required
                    == fixture["thread_routing"]["expected"]["operator_confirmation_required"]
                ),
            },
        },
        "decision_precedent": {
            "record": precedent_score.as_record(created_utc=_parse_utc("2026-07-30T12:00:00Z")),
            "expected": fixture["decision_precedent"]["expected"],
            "matches_expected": {
                "tier": precedent_score.tier == fixture["decision_precedent"]["expected"]["tier"],
                "final_score": abs(precedent_score.final_score - fixture["decision_precedent"]["expected"]["final_score"]) < 1e-9,
            },
        },
        "connector_resolution": connector_report,
    }
    if portability_report is not None:
        result["connector_portability"] = portability_report
    return result
