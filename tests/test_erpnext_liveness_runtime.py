from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import pytest

from lumina.api import config as api_config
from lumina.api import server as api_server
from lumina.business_ops.connectors.erpnext import runtime as erpnext_runtime

_SETTINGS = {
    "LUMINA_ERP_ACTOR_LIVENESS_BASE_URL": "https://erp.example.test",
    "LUMINA_ERP_ACTOR_LIVENESS_ORGANIZATION_ID": "org-1",
    "LUMINA_ERP_ACTOR_LIVENESS_SITE_ID": "site-1",
    "LUMINA_ERP_ACTOR_LIVENESS_API_KEY": "key-1",
    "LUMINA_ERP_ACTOR_LIVENESS_API_SECRET": "secret-1",
}


@pytest.mark.unit
def test_runtime_is_not_created_without_erpnext_settings() -> None:
    assert erpnext_runtime.create_erpnext_actor_liveness_runtime(environ={}) is None


@pytest.mark.unit
def test_runtime_rejects_partial_erpnext_settings() -> None:
    with pytest.raises(ValueError, match="configuration is incomplete"):
        erpnext_runtime.create_erpnext_actor_liveness_runtime(
            environ={"LUMINA_ERP_ACTOR_LIVENESS_BASE_URL": _SETTINGS["LUMINA_ERP_ACTOR_LIVENESS_BASE_URL"]}
        )


@pytest.mark.unit
def test_runtime_verifier_uses_current_credentials_and_fixed_scope() -> None:
    settings = dict(_SETTINGS)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": [{"name": "actor@example.test", "enabled": 1}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        runtime = erpnext_runtime.create_erpnext_actor_liveness_runtime(
            environ=settings,
            client=client,
        )
        assert runtime is not None
        claims = {
            "sub": "actor@example.test",
            "organization_id": "org-1",
            "site_id": "site-1",
        }

        result = runtime.verifier(claims)
        assert result.allow is True
        assert requests[0].headers["Authorization"] == "token key-1:secret-1"

        settings["LUMINA_ERP_ACTOR_LIVENESS_API_KEY"] = "key-2"
        runtime.verifier(claims)
        assert requests[1].headers["Authorization"] == "token key-2:secret-1"

        claims["site_id"] = "site-2"
        scope_result = runtime.verifier(claims)
        assert scope_result.allow is False
        assert scope_result.evidence_code == "actor_scope_mismatch"
        assert len(requests) == 2
        runtime.close()
        assert not client.is_closed


@pytest.mark.unit
def test_api_lifespan_installs_and_restores_configured_verifier(monkeypatch: pytest.MonkeyPatch) -> None:
    previous_verifier = getattr(api_config, "ACTOR_LIVENESS_VERIFIER", None)
    verifier = object()
    runtime = SimpleNamespace(verifier=verifier, closed=False)
    runtime.close = lambda: setattr(runtime, "closed", True)
    monkeypatch.setattr(
        erpnext_runtime,
        "create_erpnext_actor_liveness_runtime",
        lambda: runtime,
    )

    async def no_op() -> None:
        return None

    monkeypatch.setattr(api_server, "_start_background_tasks", no_op)
    monkeypatch.setattr(api_server, "_stop_background_tasks", no_op)

    async def exercise_lifespan() -> None:
        async with api_server._api_lifespan(api_server.app):
            assert api_config.ACTOR_LIVENESS_VERIFIER is verifier

    asyncio.run(exercise_lifespan())

    assert getattr(api_config, "ACTOR_LIVENESS_VERIFIER", None) is previous_verifier
    assert runtime.closed is True