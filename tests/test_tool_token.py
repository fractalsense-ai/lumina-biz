from __future__ import annotations

import pytest

from lumina.auth.tool_token import (
    ToolTokenError,
    mint_tool_token,
    validate_tool_token,
)


@pytest.fixture
def actor_claims() -> dict[str, str]:
    return {
        "sub": "actor-1",
        "organization_id": "org-1",
        "site_id": "site-1",
    }


@pytest.fixture
def runtime() -> dict[str, object]:
    return {
        "tool_allowlist": ["inventory.read", "inventory.update"],
        "tool_fns": {
            "inventory.read": lambda _payload: {},
            "inventory.update": lambda _payload: {},
            "admin.delete": lambda _payload: {},
        },
    }


@pytest.mark.unit
def test_tool_token_contains_only_runtime_allowlisted_tools(actor_claims, runtime) -> None:
    token = mint_tool_token(
        session_id="session-1",
        user=actor_claims,
        module_id="inventory",
        runtime=runtime,
        now=100,
    )

    assert token.allowed_tool_ids == frozenset({"inventory.read", "inventory.update"})
    assert validate_tool_token(
        token,
        session_id="session-1",
        user=actor_claims,
        module_id="inventory",
        runtime=runtime,
        now=101,
    ) == token.allowed_tool_ids


@pytest.mark.unit
@pytest.mark.parametrize(
    "field,value",
    [
        ("session_id", "session-2"),
        ("sub", "actor-2"),
        ("organization_id", "org-2"),
        ("site_id", "site-2"),
    ],
)
def test_tool_token_rejects_mismatched_scope(actor_claims, runtime, field, value) -> None:
    token = mint_tool_token(
        session_id="session-1",
        user=actor_claims,
        module_id="inventory",
        runtime=runtime,
        now=100,
    )
    current_user = dict(actor_claims)
    session_id = "session-1"
    if field == "session_id":
        session_id = value
    else:
        current_user[field] = value

    with pytest.raises(ToolTokenError):
        validate_tool_token(
            token,
            session_id=session_id,
            user=current_user,
            module_id="inventory",
            runtime=runtime,
            now=101,
        )


@pytest.mark.unit
def test_tool_token_rejects_expired_or_revoked_scope(actor_claims, runtime) -> None:
    token = mint_tool_token(
        session_id="session-1",
        user=actor_claims,
        module_id="inventory",
        runtime=runtime,
        now=100,
        ttl_seconds=5,
    )

    with pytest.raises(ToolTokenError, match="expired"):
        validate_tool_token(
            token,
            session_id="session-1",
            user=actor_claims,
            module_id="inventory",
            runtime=runtime,
            now=105,
        )

    revoked_runtime = {**runtime, "tool_allowlist": ["inventory.read"]}
    with pytest.raises(ToolTokenError, match="runtime allowlist"):
        validate_tool_token(
            token,
            session_id="session-1",
            user=actor_claims,
            module_id="inventory",
            runtime=revoked_runtime,
            now=101,
        )


@pytest.mark.unit
@pytest.mark.parametrize("missing_claim", ["sub", "organization_id", "site_id"])
def test_tool_token_requires_actor_and_operating_scope(actor_claims, runtime, missing_claim) -> None:
    incomplete_user = dict(actor_claims)
    incomplete_user.pop(missing_claim)

    with pytest.raises(ToolTokenError):
        mint_tool_token(
            session_id="session-1",
            user=incomplete_user,
            module_id="inventory",
            runtime=runtime,
            now=100,
        )