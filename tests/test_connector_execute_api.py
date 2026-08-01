"""Integration tests for tenant-enforced ERPNext fixture execution API."""
from __future__ import annotations

import importlib.util
import hashlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lumina.auth import auth
from lumina.persistence.adapter import NullPersistenceAdapter

_REPO_ROOT = Path(__file__).resolve().parents[1]


class _RecordingPersistence(NullPersistenceAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict] = []

    def append_log_record(self, session_id, record, ledger_path=None) -> None:
        self.records.append(dict(record))
        super().append_log_record(session_id, record, ledger_path)


def _load_api_module():
    module_path = _REPO_ROOT / "src" / "lumina" / "api" / "server.py"
    module_name = "lumina.api.server"
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load lumina-api-server module")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _build_embedder_stub() -> types.ModuleType:
    fake = types.ModuleType("lumina.retrieval.embedder")

    @dataclass(frozen=True)
    class _DocChunk:
        source_path: str
        heading: str
        text: str
        content_hash: str
        content_type: str = "document"
        domain_id: str | None = None
        organization_id: str | None = None
        site_id: str | None = None
        actor_id: str | None = None
        device_id: str | None = None
        record_type: str | None = None
        record_id: str | None = None
        thread_id: str | None = None
        provider: str | None = None
        external_record_type: str | None = None
        external_record_id: str | None = None
        module_key: str | None = None
        created_utc: str | None = None

        @staticmethod
        def compute_hash(content: str) -> str:
            return hashlib.sha256(content.encode("utf-8")).hexdigest()

    class _DocEmbedder:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def embed_chunks(self, chunks):
            return []

        def embed_query(self, query):
            return []

    fake.EMBEDDING_DIM = 384
    fake.DocChunk = _DocChunk
    fake.DocEmbedder = _DocEmbedder
    return fake


def _build_vector_store_stub() -> types.ModuleType:
    fake = types.ModuleType("lumina.retrieval.vector_store")

    class _SearchResult:
        def __init__(self, chunk, score: float) -> None:
            self.chunk = chunk
            self.score = score

    class _VectorStore:
        def __init__(self, *args, **kwargs) -> None:
            self.size = 0

        def load(self) -> None:
            return None

        def save(self) -> None:
            return None

        def add(self, chunks, vectors) -> None:
            self.size = len(chunks)

        def has_hash(self, _content_hash: str) -> bool:
            return False

        def search(self, *args, **kwargs):
            return []

    fake.SearchResult = _SearchResult
    fake.VectorStore = _VectorStore
    return fake


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LUMINA_RUNTIME_CONFIG_PATH", "model-packs/business-ops/cfg/runtime-config.yaml")
    monkeypatch.delenv("LUMINA_DOMAIN_REGISTRY_PATH", raising=False)
    monkeypatch.setitem(sys.modules, "lumina.retrieval.embedder", _build_embedder_stub())
    monkeypatch.setitem(sys.modules, "lumina.retrieval.vector_store", _build_vector_store_stub())
    prior_server_module = sys.modules.get("lumina.api.server")
    mod = _load_api_module()
    persistence = _RecordingPersistence()
    mod.PERSISTENCE = persistence
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    try:
        yield TestClient(mod.app), persistence
    finally:
        sys.modules.pop("lumina.api.server", None)
        if prior_server_module is not None:
            sys.modules["lumina.api.server"] = prior_server_module


def _token(*, user_id: str = "actor-a", organization_id: str | None = "org-a", site_id: str | None = "site-a") -> str:
    return auth.create_scoped_jwt(
        user_id=user_id,
        role="user",
        organization_id=organization_id,
        site_id=site_id,
    )


def _payload() -> dict:
    return {
        "request_id": "req-exec-1",
        "action_class": "query",
        "capability_namespace": "service/work-order",
        "payload": {"filters": {"status": ["=", "Open"]}},
        "actor_scope": {
            "organization_id": "org-a",
            "site_id": "site-a",
            "actor_id": "actor-a",
        },
        "session_id": "session-exec-1",
    }


@pytest.mark.integration
def test_execute_fixture_returns_scoped_success_and_trace_event(client) -> None:
    test_client, persistence = client

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token()}"},
        json=_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert isinstance(body.get("result_data"), dict)
    assert len(persistence.records) == 1
    evidence = persistence.records[0].get("evidence_summary", {})
    assert evidence["connector_operation_result"]["request_id"] == "req-exec-1"


@pytest.mark.integration
def test_execute_fixture_rejects_cross_scope_organization(client) -> None:
    test_client, _ = client
    payload = _payload()
    payload["actor_scope"]["organization_id"] = "org-b"

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token()}"},
        json=payload,
    )

    assert response.status_code == 403


@pytest.mark.integration
def test_execute_fixture_rejects_cross_scope_site(client) -> None:
    test_client, _ = client
    payload = _payload()
    payload["actor_scope"]["site_id"] = "site-b"

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token()}"},
        json=payload,
    )

    assert response.status_code == 403


@pytest.mark.integration
def test_execute_fixture_rejects_actor_mismatch(client) -> None:
    test_client, _ = client

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token(user_id='actor-z')}"},
        json=_payload(),
    )

    assert response.status_code == 403


@pytest.mark.integration
def test_execute_fixture_returns_failed_result_on_fixture_miss(client) -> None:
    test_client, _ = client
    payload = _payload()
    payload["request_id"] = "req-fixture-miss"
    payload["capability_namespace"] = "warehouse/storage"

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token()}"},
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    errors = body.get("errors")
    assert isinstance(errors, list)
    assert errors[0]["code"] == "UPSTREAM_ERROR"


@pytest.mark.integration
def test_execute_fixture_normalizes_upstream_failure_codes(client) -> None:
    test_client, _ = client
    payload = _payload()
    payload["request_id"] = "req-provider-failure"
    payload["capability_namespace"] = "logistics/dispatch"

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token()}"},
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    errors = body.get("errors")
    assert isinstance(errors, list)
    assert errors[0]["code"] == "UPSTREAM_UNAVAILABLE"
    assert errors[0]["retryable"] is True
    assert errors[0]["provider_error_code"] == "ERP-503"
