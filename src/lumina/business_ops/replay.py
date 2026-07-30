"""Deterministic Business Ops fixture replay for CI evidence."""

from __future__ import annotations

import json
from dataclasses import asdict
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
        idempotency_key=connector_fixture["idempotency_key"],
        correlation_id=connector_fixture["correlation_id"],
    )

    return {
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
        "connector_resolution": {
            "record": connector_resolution.as_record(),
            "expected": connector_fixture["expected"],
            "matches_expected": {
                "status": connector_resolution.status == connector_fixture["expected"]["status"],
                "source": connector_resolution.source == connector_fixture["expected"]["source"],
                "reason_code": connector_resolution.reason_code == connector_fixture["expected"]["reason_code"],
                "connector_instance_id": (
                    connector_resolution.connector_instance_id
                    == connector_fixture["expected"]["connector_instance_id"]
                ),
            },
        },
    }
