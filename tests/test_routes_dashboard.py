"""Tests for dashboard route endpoints: domain stats and telemetry."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lumina.auth import auth
from lumina.persistence.adapter import NullPersistenceAdapter
from lumina.core.domain_registry import DomainRegistry
from lumina.core.runtime_loader import load_runtime_context
from lumina.core.yaml_loader import load_yaml as _load_yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]


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


@pytest.fixture
def api_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LUMINA_RUNTIME_CONFIG_PATH", "model-packs/business-ops/cfg/runtime-config.yaml")
    monkeypatch.delenv("LUMINA_DOMAIN_REGISTRY_PATH", raising=False)
    mod = _load_api_module()
    mod.DOMAIN_REGISTRY = DomainRegistry(
        repo_root=_REPO_ROOT,
        single_config_path="model-packs/business-ops/cfg/runtime-config.yaml",
        load_runtime_context_fn=load_runtime_context,
    )
    mod.PERSISTENCE = NullPersistenceAdapter()
    mod.BOOTSTRAP_MODE = True
    mod._session_containers.clear()
    mod._STAGED_COMMANDS.clear()
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret-dashboard")
    mod.PERSISTENCE.load_subject_profile = _load_yaml
    return mod


@pytest.fixture
def client(api_module):
    return TestClient(api_module.app)


def _register_root(client: TestClient) -> str:
    resp = client.post(
        "/api/auth/register",
        json={"username": "admin", "password": "test-pass-123", "role": "user"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _register_user(client: TestClient, username: str = "regular", role: str = "user") -> dict:
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": "test-pass-123", "role": role},
    )
    assert resp.status_code == 200
    return resp.json()


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────
# GET /api/dashboard/domains
# ─────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestDashboardDomains:
    def test_root_can_list_domains(self, client: TestClient) -> None:
        root_token = _register_root(client)
        resp = client.get(
            "/api/dashboard/domains",
            headers=_auth_header(root_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_regular_user_forbidden(self, client: TestClient) -> None:
        _register_root(client)
        _register_user(client, "student")
        user_token = client.post(
            "/api/auth/login",
            json={"username": "student", "password": "test-pass-123"},
        ).json()["access_token"]
        resp = client.get(
            "/api/dashboard/domains",
            headers=_auth_header(user_token),
        )
        assert resp.status_code == 403

    def test_unauthenticated_rejected(self, client: TestClient) -> None:
        resp = client.get("/api/dashboard/domains")
        assert resp.status_code == 401

    def test_response_contains_expected_fields(self, client: TestClient) -> None:
        root_token = _register_root(client)
        resp = client.get(
            "/api/dashboard/domains",
            headers=_auth_header(root_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        if body:
            entry = body[0]
            assert "domain_id" in entry
            assert "name" in entry
            assert "pending_escalations" in entry
            assert "pending_ingestions" in entry
            assert "review_ingestions" in entry

    def test_admin_scope_filters_domains_and_handles_escalation_errors(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from lumina.services.dashboard import routes as dashboard_routes

        async def _admin_user(_credentials):
            return {"role": "admin", "governed_modules": ["business-ops"]}

        monkeypatch.setattr(dashboard_routes, "get_current_user", _admin_user)
        monkeypatch.setattr(dashboard_routes, "require_auth", lambda user: user)
        monkeypatch.setattr(
            dashboard_routes._cfg.DOMAIN_REGISTRY,
            "list_domains",
            lambda: [
                {"domain_id": "business-ops"},
                {"domain_id": "education", "name": "Education"},
            ],
        )

        def _raise_escalations(*args, **kwargs):
            raise RuntimeError("simulated persistence failure")

        monkeypatch.setattr(dashboard_routes._cfg.PERSISTENCE, "query_escalations", _raise_escalations)

        class _FakeIngestService:
            def list_records(self, domain_id: str, status: str):
                if status == "pending_extraction":
                    return [{"id": "p1"}]
                return [{"id": "r1"}, {"id": "r2"}]

        monkeypatch.setattr(dashboard_routes, "_get_ingest_service", lambda: _FakeIngestService())

        resp = client.get("/api/dashboard/domains")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["domain_id"] == "business-ops"
        assert body[0]["name"] == "business-ops"
        assert body[0]["version"] == "0.0.0"
        assert body[0]["pending_escalations"] == 0
        assert body[0]["pending_ingestions"] == 1
        assert body[0]["review_ingestions"] == 2

    def test_admin_without_governed_modules_gets_empty_domain_list(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from lumina.services.dashboard import routes as dashboard_routes

        async def _admin_user(_credentials):
            return {"role": "admin"}

        monkeypatch.setattr(dashboard_routes, "get_current_user", _admin_user)
        monkeypatch.setattr(dashboard_routes, "require_auth", lambda user: user)
        monkeypatch.setattr(
            dashboard_routes._cfg.DOMAIN_REGISTRY,
            "list_domains",
            lambda: [{"domain_id": "business-ops"}],
        )

        class _FakeIngestService:
            def list_records(self, domain_id: str, status: str):
                return []

        monkeypatch.setattr(dashboard_routes, "_get_ingest_service", lambda: _FakeIngestService())
        monkeypatch.setattr(
            dashboard_routes._cfg.PERSISTENCE,
            "query_escalations",
            lambda **kwargs: [],
        )

        resp = client.get("/api/dashboard/domains")
        assert resp.status_code == 200
        assert resp.json() == []


# ─────────────────────────────────────────────────────────────
# GET /api/dashboard/telemetry
# ─────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestDashboardTelemetry:
    def test_root_can_get_telemetry(self, client: TestClient) -> None:
        root_token = _register_root(client)
        resp = client.get(
            "/api/dashboard/telemetry",
            headers=_auth_header(root_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total_log_records" in body
        assert "record_type_counts" in body
        assert "escalation_summary" in body

    def test_telemetry_with_domain_filter(self, client: TestClient) -> None:
        root_token = _register_root(client)
        resp = client.get(
            "/api/dashboard/telemetry?domain_id=business-ops",
            headers=_auth_header(root_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["domain_filter"] == "business-ops"

    def test_regular_user_forbidden(self, client: TestClient) -> None:
        _register_root(client)
        _register_user(client, "viewer")
        user_token = client.post(
            "/api/auth/login",
            json={"username": "viewer", "password": "test-pass-123"},
        ).json()["access_token"]
        resp = client.get(
            "/api/dashboard/telemetry",
            headers=_auth_header(user_token),
        )
        assert resp.status_code == 403

    def test_unauthenticated_rejected(self, client: TestClient) -> None:
        resp = client.get("/api/dashboard/telemetry")
        assert resp.status_code == 401

    def test_escalation_summary_structure(self, client: TestClient) -> None:
        root_token = _register_root(client)
        resp = client.get(
            "/api/dashboard/telemetry",
            headers=_auth_header(root_token),
        )
        assert resp.status_code == 200
        esc = resp.json()["escalation_summary"]
        assert "total" in esc
        assert "pending" in esc
        assert "resolved" in esc

    def test_telemetry_handles_escalation_query_failure(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from lumina.services.dashboard import routes as dashboard_routes

        async def _root_user(_credentials):
            return {"role": "root"}

        monkeypatch.setattr(dashboard_routes, "get_current_user", _root_user)
        monkeypatch.setattr(dashboard_routes, "require_auth", lambda user: user)
        monkeypatch.setattr(
            dashboard_routes._cfg.PERSISTENCE,
            "query_log_records",
            lambda domain_id=None: [{}, {"record_type": "event"}, {"record_type": "event"}],
        )

        def _raise_escalations(*args, **kwargs):
            raise RuntimeError("simulated escalation lookup failure")

        monkeypatch.setattr(dashboard_routes._cfg.PERSISTENCE, "query_escalations", _raise_escalations)

        resp = client.get("/api/dashboard/telemetry?domain_id=business-ops")
        assert resp.status_code == 200
        body = resp.json()
        assert body["record_type_counts"]["unknown"] == 1
        assert body["record_type_counts"]["event"] == 2
        assert body["escalation_summary"] == {"total": 0, "pending": 0, "resolved": 0}

