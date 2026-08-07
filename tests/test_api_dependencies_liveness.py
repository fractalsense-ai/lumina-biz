from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

# Keep this module hermetic in environments without optional retrieval deps.
_embedder_stub = types.ModuleType("lumina.retrieval.embedder")
_embedder_stub.DocEmbedder = type("DocEmbedder", (), {})
sys.modules.setdefault("lumina.retrieval.embedder", _embedder_stub)

_vector_stub = types.ModuleType("lumina.retrieval.vector_store")
_vector_stub.VectorStore = type("VectorStore", (), {})
sys.modules.setdefault("lumina.retrieval.vector_store", _vector_stub)

_institutional_stub = types.ModuleType("lumina.retrieval.institutional")
_institutional_stub.InstitutionalMemoryIndexer = type("InstitutionalMemoryIndexer", (), {})
sys.modules.setdefault("lumina.retrieval.institutional", _institutional_stub)

from lumina.api import dependencies


@pytest.mark.unit
def test_get_active_operating_context_allows_active_actor(monkeypatch):
    persistence = MagicMock()
    persistence.get_user.return_value = {"user_id": "u-1", "active": True}

    monkeypatch.setattr(dependencies._cfg, "PERSISTENCE", persistence, raising=False)
    monkeypatch.delattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", raising=False)

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


@pytest.mark.unit
def test_get_active_operating_context_rejects_inactive_actor(monkeypatch):
    persistence = MagicMock()
    persistence.get_user.return_value = {"user_id": "u-1", "active": False}

    monkeypatch.setattr(dependencies._cfg, "PERSISTENCE", persistence, raising=False)
    monkeypatch.delattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", raising=False)

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


@pytest.mark.unit
def test_get_active_operating_context_deny_closed_when_verifier_unavailable(monkeypatch):
    def _raising_verifier(_user: dict):
        raise RuntimeError("sor timeout")

    monkeypatch.setattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", _raising_verifier, raising=False)

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


@pytest.mark.unit
def test_get_active_operating_context_uses_custom_verifier_when_configured(monkeypatch):
    calls: list[dict] = []

    def _verifier(user: dict) -> bool:
        calls.append(user)
        return True

    monkeypatch.setattr(dependencies._cfg, "ACTOR_LIVENESS_VERIFIER", _verifier, raising=False)

    user = {
        "sub": "u-1",
        "organization_id": "org-1",
        "site_id": "site-1",
        "device_id": "dev-1",
    }

    context = dependencies.get_active_operating_context(user)
    assert context["device_id"] == "dev-1"
    assert len(calls) == 1
