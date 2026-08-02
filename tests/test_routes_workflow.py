"""Tests for business-ops auto-repair workflow route endpoints."""

from __future__ import annotations

import importlib.util
import hashlib
import sys
import types
from dataclasses import dataclass
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


def _build_embedder_stub() -> types.ModuleType:
    fake = types.ModuleType("lumina.retrieval.embedder")

    @dataclass(frozen=True)
    class _DocChunk:
        source_path: str
        heading: str
        text: str
        content_hash: str

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
def api_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LUMINA_RUNTIME_CONFIG_PATH", "model-packs/business-ops/cfg/runtime-config.yaml")
    monkeypatch.delenv("LUMINA_DOMAIN_REGISTRY_PATH", raising=False)
    monkeypatch.setitem(sys.modules, "lumina.retrieval.embedder", _build_embedder_stub())
    monkeypatch.setitem(sys.modules, "lumina.retrieval.vector_store", _build_vector_store_stub())
    prior_server_module = sys.modules.get("lumina.api.server")
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
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret-workflow")
    mod.PERSISTENCE.load_subject_profile = _load_yaml
    try:
        yield mod
    finally:
        sys.modules.pop("lumina.api.server", None)
        if prior_server_module is not None:
            sys.modules["lumina.api.server"] = prior_server_module


@pytest.fixture
def client(api_module):
    return TestClient(api_module.app)


def _register_root(client: TestClient) -> str:
    resp = client.post(
        "/api/auth/register",
        json={"username": "wf-admin", "password": "test-pass-123", "role": "user"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _fake_process_message(
    session_id, message, turn_data_override, deterministic_response,
    domain_id, user, model_id, model_version, holodeck,
    physics_sandbox=None, journal_entity_salt=None, journal_mode=False,
):
    return {
        "session_id": session_id,
        "response": f"Workflow Echo: {message}",
        "action": "recommend_next_step",
        "prompt_type": "task_presentation",
        "escalated": False,
        "domain_id": domain_id or "business-ops",
        "tool_results": [],
    }


@pytest.mark.integration
class TestWorkflowRoutes:
    def test_intake_endpoint_returns_workflow_metadata(self, client: TestClient, api_module: Any) -> None:
        token = _register_root(client)
        session_id = "wf-intake-1"
        with patch("lumina.api.routes.workflow.process_message", side_effect=_fake_process_message):
            resp = client.post(
                "/api/workflow/auto-repair/intake",
                json={"session_id": session_id, "message": "Start intake"},
                headers=_auth_header(token),
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == session_id
        assert body["workflow"]["stage"] == "intake"
        assert body["workflow"]["dispatch"]["handler"] == "workflow.intake_or_status"
        assert body["workflow"]["execution"]["type"] == "step_processed"

    def test_status_endpoint_sets_stage(self, client: TestClient) -> None:
        token = _register_root(client)
        with patch("lumina.api.routes.workflow.process_message", side_effect=_fake_process_message):
            resp = client.post(
                "/api/workflow/auto-repair/status",
                json={"message": "Need status update"},
                headers=_auth_header(token),
            )
        assert resp.status_code == 200
        assert resp.json()["workflow"]["stage"] == "status"

    def test_draft_update_enforces_approval_flag(self, client: TestClient) -> None:
        token = _register_root(client)
        captured: dict[str, Any] = {}

        def _capture(*args, **kwargs):
            # process_message positional args: index 2 is turn_data_override
            captured["turn_data_override"] = args[2]
            return _fake_process_message(*args, **kwargs)

        def _draft_result(*args, **kwargs):
            captured["turn_data_override"] = args[2]
            result = _fake_process_message(*args, **kwargs)
            result["action"] = "stage_erp_draft_update"
            return result

        with patch("lumina.api.routes.workflow.process_message", side_effect=_draft_result):
            resp = client.post(
                "/api/workflow/auto-repair/draft-update",
                json={"session_id": "wf-draft-1", "message": "Please draft update"},
                headers=_auth_header(token),
            )
        assert resp.status_code == 200
        td = captured["turn_data_override"]
        assert td["packet_type"] == "customer_communication_draft"
        assert td["explicit_approval_language"] is True
        assert resp.json()["workflow"]["execution"]["type"] == "draft_staged"
        assert "draft_id" in resp.json()["workflow"]["execution"]

    def test_escalation_id_persists_across_workflow_calls(self, client: TestClient) -> None:
        token = _register_root(client)
        session_id = "wf-escalation-1"

        actions = iter(["escalate", "recommend_next_step"])

        def _sequenced(*args, **kwargs):
            result = _fake_process_message(*args, **kwargs)
            result["action"] = next(actions)
            return result

        with patch("lumina.api.routes.workflow.process_message", side_effect=_sequenced):
            first = client.post(
                "/api/workflow/auto-repair/intake",
                json={
                    "session_id": session_id,
                    "message": "Need manager review",
                    "turn_data_override": {
                        "connector_instance_id": "conn-42",
                        "connector_thread_id": "thread-19",
                    },
                },
                headers=_auth_header(token),
            )
            assert first.status_code == 200
            esc_id = first.json()["workflow"]["execution"]["escalation_record_id"]
            assert first.json()["workflow"]["next_packet"] == "escalation_record"

            second = client.post(
                "/api/workflow/auto-repair/status",
                json={"session_id": session_id, "message": "What is current status?"},
                headers=_auth_header(token),
            )
            assert second.status_code == 200
            payload = second.json()["workflow"]["dispatch"]["payload"]
            assert payload["escalation_record_id"] == esc_id
            assert payload["connector_instance_id"] == "conn-42"
            assert payload["connector_thread_id"] == "thread-19"
            assert second.json()["workflow"]["next_packet"] == "customer_communication_draft"

    def test_authentication_required(self, client: TestClient) -> None:
        resp = client.post(
            "/api/workflow/auto-repair/intake",
            json={"message": "Start intake"},
        )
        assert resp.status_code == 401
