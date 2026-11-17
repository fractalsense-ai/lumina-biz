"""Server-internal, session-bound tool capabilities."""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


class ToolTokenError(ValueError):
    """Raised when a tool capability is missing, expired, or out of scope."""


@dataclass(frozen=True)
class ToolToken:
    """In-process capability; never accept or serialize this from client input."""

    token_id: str
    session_id: str
    actor_id: str
    organization_id: str
    site_id: str
    module_id: str
    allowed_tool_ids: frozenset[str]
    issued_at: float
    expires_at: float


def _required_claim(user: Mapping[str, Any], key: str) -> str:
    value = user.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ToolTokenError(f"Tool Token requires {key}")
    return value.strip()


def _runtime_tool_ids(runtime: Mapping[str, Any]) -> frozenset[str]:
    configured = runtime.get("tool_allowlist")
    if configured is None:
        return frozenset()
    if isinstance(configured, Mapping):
        raise ToolTokenError("runtime tool allowlist must not be a mapping")
    if isinstance(configured, str):
        configured_ids = {configured.strip()} if configured.strip() else set()
    elif isinstance(configured, Iterable):
        configured_ids = {
            item.strip()
            for item in configured
            if isinstance(item, str) and item.strip()
        }
    else:
        raise ToolTokenError("runtime tool allowlist must be an iterable")

    return frozenset(configured_ids)


def mint_tool_token(
    *,
    session_id: str,
    user: Mapping[str, Any],
    module_id: str,
    runtime: Mapping[str, Any],
    now: float | None = None,
    ttl_seconds: int = 60,
) -> ToolToken:
    """Mint a short-lived internal token from an already-authorized request."""
    if not session_id.strip():
        raise ToolTokenError("Tool Token requires a session ID")
    if not module_id.strip():
        raise ToolTokenError("Tool Token requires a module ID")
    if not 1 <= ttl_seconds <= 600:
        raise ToolTokenError("Tool Token TTL must be between 1 and 600 seconds")

    issued_at = time.time() if now is None else now
    return ToolToken(
        token_id=uuid.uuid4().hex,
        session_id=session_id,
        actor_id=_required_claim(user, "sub"),
        organization_id=_required_claim(user, "organization_id"),
        site_id=_required_claim(user, "site_id"),
        module_id=module_id,
        allowed_tool_ids=_runtime_tool_ids(runtime),
        issued_at=issued_at,
        expires_at=issued_at + ttl_seconds,
    )


def validate_tool_token(
    token: ToolToken,
    *,
    session_id: str,
    user: Mapping[str, Any],
    module_id: str,
    runtime: Mapping[str, Any],
    now: float | None = None,
) -> frozenset[str]:
    """Validate token identity, lifetime, and current runtime configuration."""
    if not isinstance(token, ToolToken):
        raise ToolTokenError("Tool Token is invalid")
    current_time = time.time() if now is None else now
    if current_time < token.issued_at or current_time >= token.expires_at:
        raise ToolTokenError("Tool Token is expired or not yet valid")
    if token.session_id != session_id:
        raise ToolTokenError("Tool Token session mismatch")
    if token.actor_id != _required_claim(user, "sub"):
        raise ToolTokenError("Tool Token actor mismatch")
    if token.organization_id != _required_claim(user, "organization_id"):
        raise ToolTokenError("Tool Token organization mismatch")
    if token.site_id != _required_claim(user, "site_id"):
        raise ToolTokenError("Tool Token site mismatch")
    if token.module_id != module_id:
        raise ToolTokenError("Tool Token module mismatch")

    current_tool_ids = _runtime_tool_ids(runtime)
    if not token.allowed_tool_ids.issubset(current_tool_ids):
        raise ToolTokenError("Tool Token exceeds the current runtime allowlist")
    return token.allowed_tool_ids