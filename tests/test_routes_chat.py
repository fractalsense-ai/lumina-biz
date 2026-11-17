"""Tests for chat route endpoint: domain-resolved chat, RBAC, error handling."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

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
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret-chat")
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


def _fake_process_message(
    session_id, message, turn_data_override, deterministic_response,
    domain_id, user, model_id, model_version, holodeck,
    physics_sandbox=None, journal_entity_salt=None, journal_mode=False,
):
    """Stub for process_message that returns a valid ChatResponse dict."""
    return {
        "session_id": session_id,
        "response": f"Echo: {message}",
        "action": "continue",
        "prompt_type": "standard",
        "escalated": False,
        "domain_id": domain_id,
    }


# ─────────────────────────────────────────────────────────────
# POST /api/chat
# ─────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestChatEndpoint:
    def test_chat_passes_server_minted_tool_token_to_processing(self, client: TestClient) -> None:
        from lumina.api.routes import chat as chat_route

        actor = {
            "sub": "actor-1",
            "role": "root",
            "organization_id": "org-1",
            "site_id": "site-1",
        }
        tool_token = object()
        process_result = {
            "response": "Echo: inventory",
            "action": "continue",
            "prompt_type": "standard",
            "escalated": False,
            "domain_id": "_default",
        }
        with (
            patch.object(chat_route, "get_current_user", return_value=actor),
            patch.object(chat_route, "get_active_operating_context", return_value={
                "organization_id": "org-1",
                "site_id": "site-1",
            }),
            patch.object(chat_route, "mint_tool_token", return_value=tool_token) as mint,
            patch.object(chat_route, "process_message", return_value=process_result) as process,
        ):
            response = client.post("/api/chat", json={"message": "inventory"})

        assert response.status_code == 200
        mint.assert_called_once()
        assert process.call_args.kwargs["tool_token"] is tool_token
        assert "tool_token" not in response.json()

    def test_basic_chat_message(self, client: TestClient) -> None:
        root_token = _register_root(client)
        with patch("lumina.api.routes.chat.process_message", side_effect=_fake_process_message):
            resp = client.post(
                "/api/chat",
                json={"message": "Hello world"},
                headers=_auth_header(root_token),
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "session_id" in body
        assert body["response"] == "Echo: Hello world"
        assert body["action"] == "continue"

    def test_chat_with_explicit_domain(self, client: TestClient) -> None:
        root_token = _register_root(client)
        with patch("lumina.api.routes.chat.process_message", side_effect=_fake_process_message):
            resp = client.post(
                "/api/chat",
                json={"message": "teach me", "domain_id": "_default"},
                headers=_auth_header(root_token),
            )
        assert resp.status_code == 200

    def test_chat_with_session_id(self, client: TestClient) -> None:
        root_token = _register_root(client)
        with patch("lumina.api.routes.chat.process_message", side_effect=_fake_process_message):
            resp = client.post(
                "/api/chat",
                json={"message": "continue", "session_id": "my-session"},
                headers=_auth_header(root_token),
            )
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "my-session"

    def test_empty_message_rejected(self, client: TestClient) -> None:
        root_token = _register_root(client)
        resp = client.post(
            "/api/chat",
            json={"message": "   "},
            headers=_auth_header(root_token),
        )
        assert resp.status_code == 400

    def test_invalid_domain_rejected(self, client: TestClient) -> None:
        root_token = _register_root(client)
        resp = client.post(
            "/api/chat",
            json={"message": "hello", "domain_id": "nonexistent-domain-xyz"},
            headers=_auth_header(root_token),
        )
        assert resp.status_code == 400

    def test_holodeck_requires_elevated_role(self, client: TestClient) -> None:
        _register_root(client)
        user = _register_user(client, "student")
        user_token = client.post(
            "/api/auth/login",
            json={"username": "student", "password": "test-pass-123"},
        ).json()["access_token"]
        with patch("lumina.api.routes.chat.process_message", side_effect=_fake_process_message):
            resp = client.post(
                "/api/chat",
                json={"message": "test holodeck", "holodeck": True},
                headers=_auth_header(user_token),
            )
        assert resp.status_code == 403

    def test_holodeck_allowed_for_root(self, client: TestClient) -> None:
        root_token = _register_root(client)
        with patch("lumina.api.routes.chat.process_message", side_effect=_fake_process_message):
            resp = client.post(
                "/api/chat",
                json={"message": "holodeck sim", "holodeck": True},
                headers=_auth_header(root_token),
            )
        assert resp.status_code == 200

    def test_process_message_runtime_error_policy(self, client: TestClient) -> None:
        root_token = _register_root(client)
        with patch(
            "lumina.api.routes.chat.process_message",
            side_effect=RuntimeError("policy commitment required"),
        ):
            resp = client.post(
                "/api/chat",
                json={"message": "hello"},
                headers=_auth_header(root_token),
            )
        assert resp.status_code == 422

    def test_process_message_runtime_error_system_physics(self, client: TestClient) -> None:
        root_token = _register_root(client)
        with patch(
            "lumina.api.routes.chat.process_message",
            side_effect=RuntimeError("system_physics not committed"),
        ):
            resp = client.post(
                "/api/chat",
                json={"message": "hello"},
                headers=_auth_header(root_token),
            )
        assert resp.status_code == 503

    def test_process_message_generic_runtime_error(self, client: TestClient) -> None:
        root_token = _register_root(client)
        with patch(
            "lumina.api.routes.chat.process_message",
            side_effect=RuntimeError("something else broke"),
        ):
            resp = client.post(
                "/api/chat",
                json={"message": "hello"},
                headers=_auth_header(root_token),
            )
        assert resp.status_code == 500

    def test_process_message_generic_exception(self, client: TestClient) -> None:
        root_token = _register_root(client)
        with patch(
            "lumina.api.routes.chat.process_message",
            side_effect=ValueError("bad value"),
        ):
            resp = client.post(
                "/api/chat",
                json={"message": "hello"},
                headers=_auth_header(root_token),
            )
        assert resp.status_code == 500
