"""Shared authenticated dependencies for scope-bound API routes."""
from __future__ import annotations

import json
import logging
import functools
from typing import Any, TYPE_CHECKING

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from lumina.api import config as _cfg
from lumina.api.middleware import _bearer_scheme, get_current_user, require_auth
from lumina.auth.actor_liveness import (
    ACTOR_ACTIVE,
    ACTOR_INACTIVE,
    ACTOR_MALFORMED,
    ACTOR_UNAVAILABLE,
    ActorLivenessResult,
    validate_actor_liveness_result,
)
from lumina.auth.auth import build_token_verification_observation
from lumina.auth.operating_context import operating_context_from_claims

if TYPE_CHECKING:
    from lumina.retrieval.institutional import InstitutionalMemoryIndexer

_INSTITUTIONAL_INDEX_DIR = _cfg._REPO_ROOT / "data" / "retrieval-index" / "institutional-memory"
_ACTOR_LIVENESS_CONTRACT = "actor_liveness_enforcement_v1"
_ACTOR_LIVENESS_REASON_INACTIVE = ACTOR_INACTIVE
_ACTOR_LIVENESS_REASON_UNAVAILABLE = ACTOR_UNAVAILABLE
_ACTOR_LIVENESS_REASON_MALFORMED = ACTOR_MALFORMED

log = logging.getLogger("lumina-auth")


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """Return a verified authenticated user from the bearer-token flow."""
    return require_auth(await get_current_user(credentials))


def require_registered_domain_access(domain_id: str):
    """Build a dependency requiring membership in a mounted domain's scope."""
    async def _require_domain_access(
        user: dict[str, Any] = Depends(get_authenticated_user),
    ) -> None:
        registry = _cfg.DOMAIN_REGISTRY
        if not registry.is_multi_domain or user.get("role") == "root":
            return

        try:
            runtime = registry.get_runtime_context(domain_id)
            module_ids = set((runtime.get("module_map") or {}).keys())
            default_module_id = registry.get_default_module_id(domain_id)
            if default_module_id:
                module_ids.add(default_module_id)
        except Exception as exc:
            log.warning("Domain authorization context unavailable for %s", domain_id)
            raise HTTPException(
                status_code=503,
                detail="Domain authorization context unavailable",
            ) from exc

        domain_roles = user.get("domain_roles") or {}
        governed_modules = set(user.get("governed_modules") or [])
        if (
            domain_id in domain_roles
            or domain_id in governed_modules
            or module_ids.intersection(domain_roles)
            or module_ids.intersection(governed_modules)
        ):
            return

        raise HTTPException(status_code=403, detail=f"Access denied for domain '{domain_id}'")

    return _require_domain_access


def _emit_actor_liveness_observation(
    user: dict[str, Any],
    *,
    outcome: str,
    reason: str,
    evidence_code: str,
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
        observation["event_type"] = "actor_liveness_verification"
        observation["evidence_code"] = evidence_code
    except Exception:
        # Observability must never weaken auth-path determinism.
        observation = {
            "event_type": "actor_liveness_verification",
            "verification_source": _ACTOR_LIVENESS_CONTRACT,
            "outcome": outcome,
            "reason": reason,
            "evidence_code": evidence_code,
            "subject_present": isinstance(user.get("sub"), str),
            "organization_present": isinstance(user.get("organization_id"), str),
            "site_present": isinstance(user.get("site_id"), str),
        }
    log.info(
        "actor_liveness_observation %s",
        json.dumps(observation, separators=(",", ":"), sort_keys=True),
    )


def _default_actor_liveness_verifier(user: dict[str, Any]) -> ActorLivenessResult:
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
        return ActorLivenessResult(
            allow=False,
            deny_reason=ACTOR_INACTIVE,
            evidence_code="actor_record_missing",
        )
    active = record.get("active")
    if type(active) is not bool:
        return ActorLivenessResult(
            allow=False,
            deny_reason=ACTOR_MALFORMED,
            evidence_code="actor_active_field_malformed",
        )
    if not active:
        return ActorLivenessResult(
            allow=False,
            deny_reason=ACTOR_INACTIVE,
            evidence_code="actor_record_inactive",
        )
    return ActorLivenessResult(
        allow=True,
        deny_reason=None,
        evidence_code="actor_record_active",
    )


def _enforce_actor_liveness(user: dict[str, Any]) -> None:
    """Apply N6 actor-liveness verification with deny-closed fallback."""
    verifier = getattr(_cfg, "ACTOR_LIVENESS_VERIFIER", None)
    if verifier is None:
        verifier = _default_actor_liveness_verifier
    if not callable(verifier):
        _emit_actor_liveness_observation(
            user,
            outcome="deny",
            reason=_ACTOR_LIVENESS_REASON_UNAVAILABLE,
            evidence_code="adapter_not_callable",
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Actor liveness verification unavailable",
                "reason": _ACTOR_LIVENESS_REASON_UNAVAILABLE,
                "evidence_code": "adapter_not_callable",
                "contract": _ACTOR_LIVENESS_CONTRACT,
            },
        )

    try:
        verifier_result = verifier(user)
    except Exception:
        _emit_actor_liveness_observation(
            user,
            outcome="deny",
            reason=_ACTOR_LIVENESS_REASON_UNAVAILABLE,
            evidence_code="adapter_exception",
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Actor liveness verification unavailable",
                "reason": _ACTOR_LIVENESS_REASON_UNAVAILABLE,
                "evidence_code": "adapter_exception",
                "contract": _ACTOR_LIVENESS_CONTRACT,
            },
        )

    try:
        liveness_result = validate_actor_liveness_result(verifier_result)
    except ValueError:
        _emit_actor_liveness_observation(
            user,
            outcome="deny",
            reason=_ACTOR_LIVENESS_REASON_MALFORMED,
            evidence_code="adapter_result_malformed",
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Actor liveness verifier returned a malformed result",
                "reason": _ACTOR_LIVENESS_REASON_MALFORMED,
                "evidence_code": "adapter_result_malformed",
                "contract": _ACTOR_LIVENESS_CONTRACT,
            },
        )

    if not liveness_result.allow:
        reason = liveness_result.deny_reason or _ACTOR_LIVENESS_REASON_MALFORMED
        error_message = (
            "Actor is not active in system of record"
            if reason == _ACTOR_LIVENESS_REASON_INACTIVE
            else "Actor liveness verifier denied the actor"
        )
        _emit_actor_liveness_observation(
            user,
            outcome="deny",
            reason=reason,
            evidence_code=liveness_result.evidence_code,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": error_message,
                "reason": reason,
                "evidence_code": liveness_result.evidence_code,
                "contract": _ACTOR_LIVENESS_CONTRACT,
            },
        )

    _emit_actor_liveness_observation(
        user,
        outcome="allow",
        reason=ACTOR_ACTIVE,
        evidence_code=liveness_result.evidence_code,
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
def get_institutional_indexer() -> "InstitutionalMemoryIndexer":
    """Build and share the local institutional-memory indexer lazily."""
    from lumina.retrieval.embedder import DocEmbedder
    from lumina.retrieval.institutional import InstitutionalMemoryIndexer
    from lumina.retrieval.vector_store import VectorStore

    return InstitutionalMemoryIndexer(VectorStore(_INSTITUTIONAL_INDEX_DIR), DocEmbedder())