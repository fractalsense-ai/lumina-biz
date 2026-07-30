"""Deterministic fixture replay for slice-32 business-ops bootstrap."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
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


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = REPO_ROOT / "examples" / "business-ops-auto-repair-e2e-fixture.json"
PACK_ROOT = REPO_ROOT / "model-packs" / "business-ops"


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


@pytest.mark.unit
def test_business_ops_fixture_replay_thread_precedent_connector_flow() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    scope = fixture["scope"]

    thread_policy_cfg = yaml.safe_load((PACK_ROOT / "cfg" / "thread-routing-policy.yaml").read_text(encoding="utf-8"))
    thread_policy = resolve_thread_routing_policy(
        thread_policy_cfg,
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
    expected_thread = fixture["thread_routing"]["expected"]
    assert thread_decision.decision == expected_thread["decision"]
    assert thread_decision.thread_id == expected_thread["thread_id"]
    assert thread_decision.rationale_code == expected_thread["rationale_code"]
    assert thread_decision.operator_confirmation_required == expected_thread["operator_confirmation_required"]

    precedent_policy_cfg = yaml.safe_load((PACK_ROOT / "cfg" / "decision-precedent-policy.yaml").read_text(encoding="utf-8"))
    precedent_policy = resolve_decision_precedent_policy(
        precedent_policy_cfg,
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
    score = score_decision_precedent(
        precedent_candidates,
        precedent_policy,
        actor_id=scope["actor_id"],
        risk_class=fixture["decision_precedent"]["risk_class"],
        evaluated_utc=_parse_utc(fixture["decision_precedent"]["evaluated_utc"]),
        record_id=fixture["decision_precedent"]["record_id"],
    )
    expected_score = fixture["decision_precedent"]["expected"]
    assert score.tier == expected_score["tier"]
    assert score.final_score == pytest.approx(expected_score["final_score"])

    connector_fixture = fixture["connector_resolution"]
    entries = [
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
    resolution = resolve_connector(
        entries,
        connector_policy,
        request_id=connector_fixture["request_id"],
        actor_id=scope["actor_id"],
        action_class=connector_fixture["action_class"],
        capability_namespace=connector_fixture["capability_namespace"],
        idempotency_key=connector_fixture["idempotency_key"],
        correlation_id=connector_fixture["correlation_id"],
    )
    expected_resolution = connector_fixture["expected"]
    assert resolution.status == expected_resolution["status"]
    assert resolution.source == expected_resolution["source"]
    assert resolution.reason_code == expected_resolution["reason_code"]
    assert resolution.connector_instance_id == expected_resolution["connector_instance_id"]


@pytest.mark.unit
def test_business_ops_staging_adapter_contract_is_bounded() -> None:
    adapter = yaml.safe_load(
        (PACK_ROOT / "modules" / "auto-repair" / "tool-adapters" / "erp-draft-staging-adapter-v1.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert adapter["mode"] == "staged_only"
    assert "direct_commit" in (adapter.get("forbidden") or [])
    assert "idempotency_key" in (adapter.get("requires") or [])
