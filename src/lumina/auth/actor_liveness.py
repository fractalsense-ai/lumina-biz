"""Typed result contract for actor-liveness verifiers."""

from __future__ import annotations

import re
from dataclasses import dataclass

ACTOR_ACTIVE = "actor_active_in_sor"
ACTOR_INACTIVE = "actor_inactive_in_sor"
ACTOR_UNAVAILABLE = "actor_liveness_unavailable"
ACTOR_MALFORMED = "actor_liveness_malformed"

_VALID_DENY_REASONS = frozenset({ACTOR_INACTIVE, ACTOR_UNAVAILABLE, ACTOR_MALFORMED})
_EVIDENCE_CODE_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


@dataclass(frozen=True)
class ActorLivenessResult:
    """Deterministic adapter output; evidence_code must not contain PII."""

    allow: bool
    deny_reason: str | None
    evidence_code: str


def validate_actor_liveness_result(value: object) -> ActorLivenessResult:
    """Reject non-contract values and malformed reason/evidence fields."""
    if not isinstance(value, ActorLivenessResult) or type(value.allow) is not bool:
        raise ValueError("actor liveness result must be an ActorLivenessResult with a boolean allow field")
    if (
        not isinstance(value.evidence_code, str)
        or _EVIDENCE_CODE_PATTERN.fullmatch(value.evidence_code) is None
    ):
        raise ValueError("actor liveness result requires a stable evidence_code")
    if value.deny_reason is not None and not isinstance(value.deny_reason, str):
        raise ValueError("actor liveness result has a malformed deny_reason")
    if value.allow:
        if value.deny_reason not in (None, ACTOR_ACTIVE):
            raise ValueError("allowed actor liveness result has an invalid deny_reason")
    elif value.deny_reason not in _VALID_DENY_REASONS:
        raise ValueError("denied actor liveness result has an invalid deny_reason")
    return value