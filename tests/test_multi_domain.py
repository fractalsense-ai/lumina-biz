"""Tests for multi-domain runtime routing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lumina.auth import auth
from lumina.persistence.adapter import NullPersistenceAdapter
from lumina.core.yaml_loader import load_yaml as _load_yaml
from lumina.core.domain_registry import DomainRegistry
from lumina.core.runtime_loader import load_runtime_context

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PRIMARY_DOMAIN = "business-ops"
_ADMIN_DOMAIN = "system"


def _load_api_module(module_name: str = "lumina.api.server"):
    module_path = _REPO_ROOT / "src" / "lumina" / "api" / "server.py"
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load lumina-api-server module")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def multi_domain_module(monkeypatch: pytest.MonkeyPatch):
    """Load API module in multi-domain mode with the domain registry."""
    monkeypatch.setenv("LUMINA_DOMAIN_REGISTRY_PATH", "model-packs/system/cfg/domain-registry.yaml")
    # Ensure single-domain var is unset so registry takes precedence
    monkeypatch.delenv("LUMINA_RUNTIME_CONFIG_PATH", raising=False)

    mod = _load_api_module("lumina_api_server_multidomain_test")
    mod.PERSISTENCE = NullPersistenceAdapter()
    mod.BOOTSTRAP_MODE = False

    def _load_scoped_profile(path):
        profile = _load_yaml(path)
        if isinstance(profile, dict):
            profile["organization_id"] = "test-org"
            profile["site_id"] = "test-site"
        return profile

    mod.PERSISTENCE.load_subject_profile = _load_scoped_profile

    # Force a fresh multi-domain DomainRegistry so the test is not affected
    # by whichever DomainRegistry was cached in lumina.api.config on first import.
    mod.DOMAIN_REGISTRY = DomainRegistry(
        repo_root=_REPO_ROOT,
        registry_path="model-packs/system/cfg/domain-registry.yaml",
        load_runtime_context_fn=load_runtime_context,
    )

    # Disable SLM so tests don't require a live Ollama instance
    monkeypatch.setattr(mod, "slm_available", lambda: False)
    monkeypatch.setattr("lumina.api.processing.slm_available", lambda: False)

    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret")
    return mod


@pytest.fixture
def multi_client(multi_domain_module):
    return TestClient(multi_domain_module.app)


# ── Domain catalog ───────────────────────────────────────────


@pytest.mark.integration
def test_domains_endpoint_lists_available_domains(multi_client: TestClient) -> None:
    resp = multi_client.get("/api/domains")
    assert resp.status_code == 200
    domains = resp.json()
    domain_ids = [d["domain_id"] for d in domains]
    assert _PRIMARY_DOMAIN in domain_ids
    assert _ADMIN_DOMAIN in domain_ids


@pytest.mark.integration
def test_domain_info_with_explicit_domain(multi_client: TestClient) -> None:
    resp = multi_client.get("/api/domain-info", params={"domain_id": _PRIMARY_DOMAIN})
    assert resp.status_code == 200
    body = resp.json()
    assert body["domain_id"]


@pytest.mark.integration
def test_domain_info_invalid_domain_returns_400(multi_client: TestClient) -> None:
    resp = multi_client.get("/api/domain-info", params={"domain_id": "nonexistent"})
    assert resp.status_code == 400


# ── Per-session domain binding ───────────────────────────────


@pytest.mark.integration
def test_chat_with_explicit_domain_id(multi_client: TestClient) -> None:
    resp = multi_client.post(
        "/api/chat",
        json={
            "message": "Hello from business ops domain",
            "deterministic_response": True,
            "domain_id": _PRIMARY_DOMAIN,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["domain_id"] == _PRIMARY_DOMAIN


@pytest.mark.integration
def test_chat_uses_default_domain_when_omitted(multi_client: TestClient) -> None:
    """Unauthenticated request with no domain_id falls back to global default."""
    resp = multi_client.post(
        "/api/chat",
        json={
            "message": "Hello with no domain specified",
            "deterministic_response": True,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    # Unauthenticated users → global default_domain in domain-registry.yaml
    assert body["domain_id"] == _PRIMARY_DOMAIN


@pytest.mark.integration
def test_chat_invalid_domain_returns_400(multi_client: TestClient) -> None:
    resp = multi_client.post(
        "/api/chat",
        json={
            "message": "Hello",
            "deterministic_response": True,
            "domain_id": "nonexistent_domain",
        },
    )
    assert resp.status_code == 400
    assert "nonexistent_domain" in resp.text


@pytest.mark.integration
def test_session_domain_switch(multi_client: TestClient) -> None:
    """A privileged session can switch between active domains mid-session."""
    token = _make_token(None, "root")

    # First turn: start in business-ops domain
    resp1 = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": "domain-switch-test",
            "message": "First turn in business-ops",
            "deterministic_response": True,
            "domain_id": _PRIMARY_DOMAIN,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert resp1.status_code == 200
    assert resp1.json()["domain_id"] == _PRIMARY_DOMAIN

    # Second turn: switch to system — should succeed for root
    resp2 = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": "domain-switch-test",
            "message": "Switching to system",
            "deterministic_response": True,
            "domain_id": _ADMIN_DOMAIN,
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["domain_id"] == _ADMIN_DOMAIN

    # Third turn: switch back to business-ops — should resume
    resp3 = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": "domain-switch-test",
            "message": "Back to business-ops",
            "deterministic_response": True,
            "domain_id": _PRIMARY_DOMAIN,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert resp3.status_code == 200
    assert resp3.json()["domain_id"] == _PRIMARY_DOMAIN


@pytest.mark.integration
def test_parallel_sessions_different_domains(multi_client: TestClient) -> None:
    """Two sessions can run concurrently on different domains for root."""
    token = _make_token(None, "root")

    edu_resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": "parallel-edu",
            "message": "Business-ops turn",
            "deterministic_response": True,
            "domain_id": _PRIMARY_DOMAIN,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert edu_resp.status_code == 200
    assert edu_resp.json()["domain_id"] == _PRIMARY_DOMAIN

    agri_resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": "parallel-agri",
            "message": "System turn",
            "deterministic_response": True,
            "domain_id": _ADMIN_DOMAIN,
        },
    )
    assert agri_resp.status_code == 200
    assert agri_resp.json()["domain_id"] == _ADMIN_DOMAIN

    # Confirm each session is isolated (second turn still works on own domain)
    edu_resp2 = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_id": "parallel-edu",
            "message": "Business-ops turn 2",
            "deterministic_response": True,
            "domain_id": _PRIMARY_DOMAIN,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert edu_resp2.status_code == 200
    assert edu_resp2.json()["domain_id"] == _PRIMARY_DOMAIN


# ── Role-based default domain routing ────────────────────────


def _make_token(mod, role: str, governed_modules: list[str] | None = None) -> str:
    """Create a signed JWT for the given role using the test JWT_SECRET."""
    return auth.create_jwt(
        user_id=f"test_{role}_001",
        role=role,
        governed_modules=governed_modules or [],
    )


@pytest.mark.integration
def test_root_defaults_to_system_domain(multi_client: TestClient) -> None:
    """Authenticated root user with no domain_id routes to the system domain."""
    token = _make_token(None, "root")
    resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Show me the current System Log configuration",
            "deterministic_response": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["domain_id"] == "system"


@pytest.mark.integration
def test_it_support_defaults_to_system_domain(multi_client: TestClient) -> None:
    """Authenticated super_admin user with no domain_id routes to the system domain."""
    token = _make_token(None, "super_admin")
    resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Diagnose this session",
            "deterministic_response": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["domain_id"] == "system"


@pytest.mark.integration
def test_qa_defaults_to_global_default_domain(multi_client: TestClient) -> None:
    """Authenticated operator user with no domain_id falls back to global default."""
    token = _make_token(None, "operator")
    resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Run a test",
            "deterministic_response": True,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["domain_id"] == _PRIMARY_DOMAIN


@pytest.mark.integration
def test_auditor_defaults_to_global_default_domain(multi_client: TestClient) -> None:
    """Authenticated half_operator user with no domain_id falls back to global default."""
    token = _make_token(None, "half_operator")
    resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Audit something",
            "deterministic_response": True,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["domain_id"] == _PRIMARY_DOMAIN


@pytest.mark.integration
def test_domain_authority_defaults_to_governed_domain(multi_client: TestClient) -> None:
    """admin user routes to the domain matching their governed_modules."""
    token = _make_token(None, "admin", governed_modules=["domain/bizops/auto-repair/v1"])
    resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Let me review my module",
            "deterministic_response": True,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["domain_id"] == _PRIMARY_DOMAIN


@pytest.mark.integration
def test_domain_authority_no_governed_modules_uses_global_default(multi_client: TestClient) -> None:
    """admin with empty governed_modules falls back to global default."""
    token = _make_token(None, "admin", governed_modules=[])
    resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Hello",
            "deterministic_response": True,
            "turn_data_override": {
                "contains_high_risk_terms": False,
                "explicit_approval_language": False,
                "off_task_ratio": 0.0,
                "response_latency_sec": 5,
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["domain_id"] == _PRIMARY_DOMAIN


@pytest.mark.integration
def test_system_role_user_can_access_system_domain_when_explicit(
    multi_client: TestClient,
) -> None:
    """system domain explicit request from root user reaches system domain."""
    token = _make_token(None, "root")
    resp = multi_client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Tell me about RBAC",
            "deterministic_response": True,
            "domain_id": "system",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["domain_id"] == "system"

