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
from lumina.business_ops.connectors.transport import ConnectorTransportResponse
from lumina.orchestrator.system_log_writer import hash_record

_REPO_ROOT = Path(__file__).resolve().parents[1]


class _RecordingPersistence(NullPersistenceAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict] = []
        self.create_user(
            "actor-a",
            "actor-a",
            "hash",
            "user",
            active=True,
        )

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


class _ScanAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.error: dict[str, object] | None = None

    def lookup(self, search_value: str, *, organization_id: str, site_id: str):
        self.calls.append((search_value, organization_id, site_id))
        return ConnectorTransportResponse(
            status_code=403 if self.error else 200,
            payload=None if self.error else {"message": {"item_code": "ITEM-1", "barcode": "BAR-1"}},
            correlation_id="inventory-scan-test",
            attempts=1,
            error=self.error,
        )


@pytest.mark.integration
def test_erpnext_inventory_scan_returns_result_and_trace_event(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, persistence = client
    adapter = _ScanAdapter()
    from lumina.api import config as api_config
    monkeypatch.setattr(api_config, "ERPNext_INVENTORY_SCAN_ADAPTER", adapter, raising=False)

    response = test_client.post(
        "/api/connectors/erpnext/scan",
        headers={"Authorization": f"Bearer {_token()}"},
        json={"search_value": " BAR-1 ", "session_id": "session-scan-1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["payload"] == {"message": {"item_code": "ITEM-1", "barcode": "BAR-1"}}
    assert adapter.calls == [(" BAR-1 ", "org-a", "site-a")]
    assert len(persistence.records) == 1
    evidence = persistence.records[0].get("evidence_summary", {})
    assert evidence["correlation_id"] == "inventory-scan-test"


@pytest.mark.integration
def test_erpnext_inventory_scan_requires_configured_adapter(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, _ = client
    from lumina.api import config as api_config
    monkeypatch.delattr(api_config, "ERPNext_INVENTORY_SCAN_ADAPTER", raising=False)

    response = test_client.post(
        "/api/connectors/erpnext/scan",
        headers={"Authorization": f"Bearer {_token()}"},
        json={"search_value": "BAR-1"},
    )

    assert response.status_code == 503


@pytest.mark.integration
def test_erpnext_inventory_scan_rejects_whitespace(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, _ = client
    adapter = _ScanAdapter()
    from lumina.api import config as api_config
    monkeypatch.setattr(api_config, "ERPNext_INVENTORY_SCAN_ADAPTER", adapter, raising=False)

    response = test_client.post(
        "/api/connectors/erpnext/scan",
        headers={"Authorization": f"Bearer {_token()}"},
        json={"search_value": "   "},
    )

    assert response.status_code == 422
    assert adapter.calls == []


@pytest.mark.integration
def test_erpnext_inventory_scan_rejects_traversal_session_id(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, _ = client
    adapter = _ScanAdapter()
    from lumina.api import config as api_config
    monkeypatch.setattr(api_config, "ERPNext_INVENTORY_SCAN_ADAPTER", adapter, raising=False)

    response = test_client.post(
        "/api/connectors/erpnext/scan",
        headers={"Authorization": f"Bearer {_token()}"},
        json={"search_value": "BAR-1", "session_id": "x/../../../outside"},
    )

    assert response.status_code == 422
    assert adapter.calls == []


@pytest.mark.integration
def test_erpnext_inventory_scan_repeated_session_hash_chain(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, persistence = client
    adapter = _ScanAdapter()
    from lumina.api import config as api_config
    monkeypatch.setattr(api_config, "ERPNext_INVENTORY_SCAN_ADAPTER", adapter, raising=False)

    for _ in range(2):
        response = test_client.post(
            "/api/connectors/erpnext/scan",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"search_value": "BAR-1", "session_id": "scan-session-chain"},
        )
        assert response.status_code == 200

    assert len(persistence.records) == 2
    assert persistence.records[0]["prev_record_hash"] == "genesis"
    assert persistence.records[1]["prev_record_hash"] == hash_record(persistence.records[0])


@pytest.mark.integration
def test_erpnext_inventory_scan_rejects_cross_scope(client, monkeypatch: pytest.MonkeyPatch) -> None:
    test_client, persistence = client
    adapter = _ScanAdapter()
    adapter.error = {
        "code": "SCOPE_MISMATCH",
        "message": "Inventory scan is outside the configured organization and site scope",
        "severity": "critical",
        "retryable": False,
    }
    from lumina.api import config as api_config
    monkeypatch.setattr(api_config, "ERPNext_INVENTORY_SCAN_ADAPTER", adapter, raising=False)

    response = test_client.post(
        "/api/connectors/erpnext/scan",
        headers={"Authorization": f"Bearer {_token(organization_id='org-b', site_id='site-a')}"},
        json={"search_value": "BAR-1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["error"]["code"] == "SCOPE_MISMATCH"
    assert body["error"]["retryable"] is False
    assert adapter.calls == [("BAR-1", "org-b", "site-a")]
    assert len(persistence.records) == 1


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
def test_execute_fixture_accepts_canonical_pos_cancellation_and_returns_structured_unsupported(client) -> None:
    test_client, _ = client
    payload = _payload()
    payload["request_id"] = "req-pos-cancel-unsupported"
    payload["action_class"] = "request_cancel"
    payload["capability_namespace"] = "sales/pos"

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token()}"},
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["action_class"] == "request_cancel"
    assert body["capability_namespace"] == "sales/pos"
    assert body["status"] == "failed"
    assert body["errors"]


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


@pytest.mark.integration
@pytest.mark.parametrize(
    "capability_namespace,organization_id,site_id,expected_code,expected_retryable,expected_provider_code",
    [
        ("inventory", "org-rate-limited", "site-rate-limited", "RATE_LIMITED", True, "ERP-429"),
        ("scheduling", "org-validation", "site-validation", "VALIDATION_FAILED", False, "ERP-400"),
        ("service/work-order", "org-auth", "site-auth", "AUTH_FAILED", False, "ERP-401"),
    ],
)
def test_execute_fixture_normalizes_additional_endpoint_failures(
    client,
    capability_namespace: str,
    organization_id: str,
    site_id: str,
    expected_code: str,
    expected_retryable: bool,
    expected_provider_code: str,
) -> None:
    test_client, _ = client
    payload = {
        "request_id": f"req-{expected_code.lower()}",
        "action_class": "query",
        "capability_namespace": capability_namespace,
        "payload": {"filters": {}},
        "actor_scope": {
            "organization_id": organization_id,
            "site_id": site_id,
            "actor_id": "actor-a",
        },
    }

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token(organization_id=organization_id, site_id=site_id)}"},
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    errors = body.get("errors")
    assert isinstance(errors, list)
    assert errors[0]["code"] == expected_code
    assert errors[0]["retryable"] is expected_retryable
    assert errors[0]["provider_error_code"] == expected_provider_code


@pytest.mark.integration
def test_execute_fixture_returns_canonical_error_for_unsupported_mapping(client) -> None:
    test_client, _ = client
    payload = {
        "request_id": "req-unsupported-mapping",
        "action_class": "create_draft",
        "capability_namespace": "inventory",
        "payload": {"record": {"item_code": "SKU-9"}},
        "actor_scope": {
            "organization_id": "org-a",
            "site_id": "site-a",
            "actor_id": "actor-a",
        },
    }

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
    assert errors[0]["code"] == "UNSUPPORTED_MAPPING"
    assert errors[0]["retryable"] is False
    assert errors[0]["severity"] == "warning"
    assert errors[0]["action_class"] == "create_draft"
    assert errors[0]["capability_namespace"] == "inventory"


@pytest.mark.integration
def test_execute_fixture_requires_actor_scope_payload(client) -> None:
    test_client, _ = client
    payload = {
        "request_id": "req-no-actor-scope",
        "action_class": "query",
        "capability_namespace": "inventory",
        "payload": {"filters": {}},
        "session_id": "session-exec-missing-scope",
    }

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token()}"},
        json=payload,
    )

    assert response.status_code == 422
    detail = response.json().get("detail")
    assert isinstance(detail, list)
    assert any("actor_scope" in str(item.get("loc", [])) for item in detail if isinstance(item, dict))


@pytest.mark.integration
def test_execute_fixture_rejects_invalid_capability_namespace(client) -> None:
    test_client, _ = client
    payload = _payload()
    payload["capability_namespace"] = "custom/non-canonical"

    response = test_client.post(
        "/api/connectors/erpnext/execute-fixture",
        headers={"Authorization": f"Bearer {_token()}"},
        json=payload,
    )

    assert response.status_code == 422
    detail = response.json().get("detail")
    assert isinstance(detail, list)
    assert any(
        "capability_namespace" in str(item.get("loc", []))
        for item in detail
        if isinstance(item, dict)
    )
