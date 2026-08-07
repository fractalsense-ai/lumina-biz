"""Shared authenticated dependencies for scope-bound API routes."""
from __future__ import annotations

import json
import logging
import functools
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from lumina.api import config as _cfg
from lumina.api.middleware import _bearer_scheme, get_current_user, require_auth
from lumina.auth.auth import build_token_verification_observation
from lumina.auth.operating_context import operating_context_from_claims
from lumina.retrieval.embedder import DocEmbedder
from lumina.retrieval.institutional import InstitutionalMemoryIndexer
from lumina.retrieval.vector_store import VectorStore

_INSTITUTIONAL_INDEX_DIR = _cfg._REPO_ROOT / "data" / "retrieval-index" / "institutional-memory"
_ACTOR_LIVENESS_CONTRACT = "actor_liveness_enforcement_v1"
_ACTOR_LIVENESS_REASON_INACTIVE = "actor_inactive_in_sor"
_ACTOR_LIVENESS_REASON_UNAVAILABLE = "actor_liveness_unavailable"

log = logging.getLogger("lumina-auth")


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """Return a verified authenticated user from the bearer-token flow."""
    return require_auth(await get_current_user(credentials))


def _emit_actor_liveness_observation(
    user: dict[str, Any],
    *,
    outcome: str,
    reason: str,
) -> None:
    """Emit pseudonymous actor-liveness observability fields."""
    try:
        observation = build_token_verification_observation(
            outcome=outcome,
            reason=reason,
            verification_source=_ACTOR_LIVENESS_CONTRACT,
            issuer=user.get("iss") if isinstance(user.get("iss"), str) else None,
            audience=user.get("aud") if isinstance(user.get("aud"), str) else None,
            token_scope=user.get("token_scope") if isinstance(user.get("token_scope"), str) else None,
            jti=user.get("jti") if isinstance(user.get("jti"), str) else None,
            subject=user.get("sub") if isinstance(user.get("sub"), str) else None,
            organization_id=(
                user.get("organization_id") if isinstance(user.get("organization_id"), str) else None
            ),
            site_id=user.get("site_id") if isinstance(user.get("site_id"), str) else None,
        )
    except Exception:
        # Observability must never weaken auth-path determinism.
        observation = {
            "event_type": "actor_liveness_verification",
            "verification_source": _ACTOR_LIVENESS_CONTRACT,
            "outcome": outcome,
            "reason": reason,
            "subject_present": isinstance(user.get("sub"), str),
            "organization_present": isinstance(user.get("organization_id"), str),
            "site_present": isinstance(user.get("site_id"), str),
        }
    log.info(
        "actor_liveness_observation %s",
        json.dumps(observation, separators=(",", ":"), sort_keys=True),
    )


def _default_actor_liveness_verifier(user: dict[str, Any]) -> bool:
    """Return True when actor is active in the current System of Record.

    Uses persistence user state as SoR authority for local/runtime verification.
    """
    subject = user.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("authenticated actor is missing subject id")

    persistence = getattr(_cfg, "PERSISTENCE", None)
    if persistence is None:
        raise RuntimeError("persistence backend unavailable")

    get_user = getattr(persistence, "get_user", None)
    if not callable(get_user):
        raise RuntimeError("persistence backend does not expose get_user")

    record = get_user(subject)
    if record is None:
        return False
    return bool(record.get("active", False))


def _enforce_actor_liveness(user: dict[str, Any]) -> None:
    """Apply N6 actor-liveness verification with deny-closed fallback."""
    verifier = getattr(_cfg, "ACTOR_LIVENESS_VERIFIER", None)
    if verifier is None:
        verifier = _default_actor_liveness_verifier
    if not callable(verifier):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Actor liveness verification unavailable",
                "reason": _ACTOR_LIVENESS_REASON_UNAVAILABLE,
                "contract": _ACTOR_LIVENESS_CONTRACT,
            },
        )

    try:
        is_active = bool(verifier(user))
    except Exception:
        _emit_actor_liveness_observation(
            user,
            outcome="deny",
            reason=_ACTOR_LIVENESS_REASON_UNAVAILABLE,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Actor liveness verification unavailable",
                "reason": _ACTOR_LIVENESS_REASON_UNAVAILABLE,
                "contract": _ACTOR_LIVENESS_CONTRACT,
            },
        )

    if not is_active:
        _emit_actor_liveness_observation(
            user,
            outcome="deny",
            reason=_ACTOR_LIVENESS_REASON_INACTIVE,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Actor is not active in system of record",
                "reason": _ACTOR_LIVENESS_REASON_INACTIVE,
                "contract": _ACTOR_LIVENESS_CONTRACT,
            },
        )

    _emit_actor_liveness_observation(
        user,
        outcome="allow",
        reason="actor_active_in_sor",
    )


def get_active_operating_context(
    user: dict[str, Any] = Depends(get_authenticated_user),
) -> dict[str, str | None]:
    """Require an active organization and site for scope-bound operations."""
    _enforce_actor_liveness(user)
    try:
        context = operating_context_from_claims(user)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid active operating context") from exc
    if context is None:
        raise HTTPException(status_code=403, detail="An active organization and site context is required")
    return context


@functools.lru_cache(maxsize=1)
def get_institutional_indexer() -> InstitutionalMemoryIndexer:
    """Build and share the local institutional-memory indexer lazily."""
    return InstitutionalMemoryIndexer(VectorStore(_INSTITUTIONAL_INDEX_DIR), DocEmbedder())