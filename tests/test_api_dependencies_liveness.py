from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from lumina.api import dependencies
from lumina.auth.actor_liveness import ActorLivenessResult


def _extract_actor_liveness_events(caplog: pytest.LogCaptureFixture) -> list[dict]:
    events: list[dict] = []
    for rec in caplog.records:
        if rec.name != "lumina-auth":
            continue
        msg = rec.getMessage()
        if not msg.startswith("actor_liveness_observation "):
            continue
        events.append(json.loads(msg.split("actor_liveness_observation ", 1)[1]))
    return events


@pytest.mark.unit
def test_get_active_operating_context_allows_active_actor(monkeypatch, caplog):
    persistence = MagicMock()
    persistence.get_user.return_value = {"user_id": "u-1", "active": True}

    caplog.set_level(logging.INFO, logger="lumina-auth")
    monkeypatch.setattr(dependencies._cfg, "PERSISTENCE", persistence, raising=False)
    monkeypatch.delattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", raising=False)
    monkeypatch.setattr(dependencies, "build_token_verification_observation", lambda **kwargs: {
        "event_type": "token_verification",
        "verification_source": kwargs["verification_source"],
        "outcome": kwargs["outcome"],
        "reason": kwargs["reason"],
        "subject_hash": "abc123hash",
        "jti_hash": "def456hash",
        "organization_hash": "ghi789hash",
        "site_hash": "jkl012hash",
    })

    user = {
        "sub": "u-1",
        "organization_id": "org-1",
        "site_id": "site-1",
        "iss": "lumina",
        "jti": "tok-1",
        "token_scope": "domain",
    }

    context = dependencies.get_active_operating_context(user)
    assert context["organization_id"] == "org-1"
    assert context["site_id"] == "site-1"

    events = _extract_actor_liveness_events(caplog)
    assert len(events) == 1
    event = events[0]
    assert event["outcome"] == "allow"
    assert event["reason"] == "actor_active_in_sor"
    assert event["subject_hash"] == "abc123hash"
    assert event["jti_hash"] == "def456hash"
    assert "u-1" not in json.dumps(event)
    assert "tok-1" not in json.dumps(event)


@pytest.mark.unit
def test_get_active_operating_context_rejects_inactive_actor(monkeypatch, caplog):
    persistence = MagicMock()
    persistence.get_user.return_value = {"user_id": "u-1", "active": False}

    caplog.set_level(logging.INFO, logger="lumina-auth")
    monkeypatch.setattr(dependencies._cfg, "PERSISTENCE", persistence, raising=False)
    monkeypatch.delattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", raising=False)
    monkeypatch.setattr(dependencies, "build_token_verification_observation", lambda **kwargs: {
        "event_type": "token_verification",
        "verification_source": kwargs["verification_source"],
        "outcome": kwargs["outcome"],
        "reason": kwargs["reason"],
        "subject_hash": "inactivehash",
        "organization_hash": "orghash",
        "site_hash": "sitehash",
    })

    user = {
        "sub": "u-1",
        "organization_id": "org-1",
        "site_id": "site-1",
    }

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_active_operating_context(user)

    assert exc_info.value.status_code == 403
    detail = exc_info.value.detail
    assert detail["reason"] == "actor_inactive_in_sor"
    assert detail["contract"] == "actor_liveness_enforcement_v1"

    events = _extract_actor_liveness_events(caplog)
    assert len(events) == 1
    event = events[0]
    assert event["outcome"] == "deny"
    assert event["reason"] == "actor_inactive_in_sor"
    assert event["subject_hash"] == "inactivehash"
    assert "u-1" not in json.dumps(event)


@pytest.mark.unit
def test_get_active_operating_context_deny_closed_when_verifier_unavailable(monkeypatch, caplog):
    def _raising_verifier(_user: dict):
        raise RuntimeError("sor timeout")

    caplog.set_level(logging.INFO, logger="lumina-auth")
    monkeypatch.setattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", _raising_verifier, raising=False)
    monkeypatch.setattr(dependencies, "build_token_verification_observation", lambda **kwargs: {
        "event_type": "token_verification",
        "verification_source": kwargs["verification_source"],
        "outcome": kwargs["outcome"],
        "reason": kwargs["reason"],
        "subject_hash": "timeout-hash",
    })

    user = {
        "sub": "u-1",
        "organization_id": "org-1",
        "site_id": "site-1",
    }

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_active_operating_context(user)

    assert exc_info.value.status_code == 403
    detail = exc_info.value.detail
    assert detail["reason"] == "actor_liveness_unavailable"
    assert detail["contract"] == "actor_liveness_enforcement_v1"

    events = _extract_actor_liveness_events(caplog)
    assert len(events) == 1
    event = events[0]
    assert event["outcome"] == "deny"
    assert event["reason"] == "actor_liveness_unavailable"
    assert event["subject_hash"] == "timeout-hash"


@pytest.mark.unit
def test_get_active_operating_context_denies_closed_on_verifier_timeout(monkeypatch, caplog):
    def _timeout_verifier(_user: dict):
        raise TimeoutError("actor liveness timed out")

    caplog.set_level(logging.INFO, logger="lumina-auth")
    monkeypatch.setattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", _timeout_verifier, raising=False)
    monkeypatch.setattr(dependencies, "build_token_verification_observation", lambda **kwargs: {
        "event_type": "actor_liveness_verification",
        "verification_source": kwargs["verification_source"],
        "outcome": kwargs["outcome"],
        "reason": kwargs["reason"],
        "subject_hash": "timeout-hash",
    })

    user = {
        "sub": "u-1",
        "organization_id": "org-1",
        "site_id": "site-1",
    }

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_active_operating_context(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["reason"] == "actor_liveness_unavailable"
    events = _extract_actor_liveness_events(caplog)
    assert len(events) == 1
    assert events[0]["outcome"] == "deny"
    assert events[0]["reason"] == "actor_liveness_unavailable"
    assert events[0]["subject_hash"] == "timeout-hash"


@pytest.mark.unit
def test_get_active_operating_context_deny_closed_for_non_callable_verifier(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="lumina-auth")
    monkeypatch.setattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", "not-callable", raising=False)
    monkeypatch.setattr(dependencies, "build_token_verification_observation", lambda **kwargs: {
        "event_type": "token_verification",
        "verification_source": kwargs["verification_source"],
        "outcome": kwargs["outcome"],
        "reason": kwargs["reason"],
        "subject_hash": "noncall-hash",
    })

    user = {
        "sub": "u-1",
        "organization_id": "org-1",
        "site_id": "site-1",
    }

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_active_operating_context(user)

    assert exc_info.value.status_code == 403
    detail = exc_info.value.detail
    assert detail["reason"] == "actor_liveness_unavailable"
    assert detail["contract"] == "actor_liveness_enforcement_v1"

    events = _extract_actor_liveness_events(caplog)
    assert len(events) == 1
    event = events[0]
    assert event["outcome"] == "deny"
    assert event["reason"] == "actor_liveness_unavailable"
    assert event["subject_hash"] == "noncall-hash"


@pytest.mark.unit
def test_get_active_operating_context_uses_structured_custom_verifier(monkeypatch, caplog):
    from lumina.auth.actor_liveness import ActorLivenessResult

    calls: list[dict] = []

    def _verifier(user: dict) -> ActorLivenessResult:
        calls.append(user)
        return ActorLivenessResult(
            allow=True,
            deny_reason=None,
            evidence_code="membership_active",
        )

    caplog.set_level(logging.INFO, logger="lumina-auth")
    monkeypatch.setattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", _verifier, raising=False)
    monkeypatch.setattr(dependencies, "build_token_verification_observation", lambda **kwargs: {
        "event_type": "actor_liveness_verification",
        "verification_source": kwargs["verification_source"],
        "outcome": kwargs["outcome"],
        "reason": kwargs["reason"],
        "evidence_code": kwargs.get("evidence_code"),
        "subject_hash": "active-hash",
    })

    user = {
        "sub": "u-1",
        "organization_id": "org-1",
        "site_id": "site-1",
        "device_id": "dev-1",
    }

    context = dependencies.get_active_operating_context(user)
    assert context["device_id"] == "dev-1"
    assert len(calls) == 1
    events = _extract_actor_liveness_events(caplog)
    assert len(events) == 1
    assert events[0]["evidence_code"] == "membership_active"


@pytest.mark.unit
@pytest.mark.parametrize(
    "invalid_result",
    [
        "true",
        ActorLivenessResult(allow=1, deny_reason=None, evidence_code="active"),
        ActorLivenessResult(allow=True, deny_reason="actor_inactive_in_sor", evidence_code="active"),
        ActorLivenessResult(allow=False, deny_reason="actor_inactive_in_sor", evidence_code=""),
        ActorLivenessResult(allow=False, deny_reason=[], evidence_code="adapter_denied"),
        ActorLivenessResult(allow=True, deny_reason=None, evidence_code="actor@example.com"),
    ],
)
def test_get_active_operating_context_rejects_malformed_verifier_result(
    invalid_result,
    monkeypatch,
    caplog,
):
    caplog.set_level(logging.INFO, logger="lumina-auth")

    def _invalid_verifier(_user: dict):
        return invalid_result

    monkeypatch.setattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", _invalid_verifier, raising=False)
    monkeypatch.setattr(dependencies, "build_token_verification_observation", lambda **kwargs: {
        "event_type": "actor_liveness_verification",
        "verification_source": kwargs["verification_source"],
        "outcome": kwargs["outcome"],
        "reason": kwargs["reason"],
        "subject_hash": "invalid-bool-hash",
    })

    user = {
        "sub": "u-1",
        "organization_id": "org-1",
        "site_id": "site-1",
    }

    with pytest.raises(HTTPException) as exc_info:
        dependencies.get_active_operating_context(user)

    assert exc_info.value.status_code == 403
    detail = exc_info.value.detail
    assert detail["reason"] == "actor_liveness_malformed"

    events = _extract_actor_liveness_events(caplog)
    assert len(events) == 1
    event = events[0]
    assert event["outcome"] == "deny"
    assert event["reason"] == "actor_liveness_malformed"
    assert event["evidence_code"] == "adapter_result_malformed"
