---
version: 1.0.0
last_updated: 2026-08-05
---

# auth(3)

**Version:** 1.3.0
**Status:** Active
**Last updated:** 2026-08-05

---

## NAME

`auth.py` — JWT authentication and password hashing

## SYNOPSIS

```python
from auth import create_jwt, verify_jwt, hash_password, verify_password
```

## FUNCTIONS

### `create_jwt(user_id, role, governed_modules, domain_roles=None, ttl_minutes=None) → str`

Create a signed JWT containing user identity and RBAC claims.

**Claims:** `sub` (user_id), `role`, `governed_modules`, `domain_roles` (optional), `iss` ("lumina"), `iat`, `exp`

**Parameters:**
- `domain_roles` — optional `dict[str, str]` mapping domain module IDs to domain-scoped role IDs (e.g., `{"domain/bizops/algebra-level-1/v1": "teaching_assistant"}`). Omitted from the token payload when `None` or empty.

### `verify_jwt(token) → dict`

Decode and verify a JWT. Returns the payload dict.

**Raises:** `TokenExpiredError`, `TokenInvalidError`

### `hash_password(password) → str`

Hash a password using the configured algorithm. Default: Argon2id.

Supported algorithms (set via `LUMINA_PASSWORD_HASH_ALGORITHM`):

| Algorithm | Format | Library required |
|-----------|--------|-----------------|
| `argon2id` (default) | `$argon2id$v=19$m=...,t=...,p=...$salt$hash` | `argon2-cffi` |
| `bcrypt` | `$2b$cost$salthash` | `bcrypt` |
| `sha256` | `salt:hash` | none (stdlib) |

Falls back gracefully when libraries are missing: argon2id → bcrypt → sha256.

### `verify_password(password, stored) → bool`

Verify a password against a stored hash string. Auto-detects the hashing
algorithm from the stored format — no configuration needed for verification.

## CONSTANTS

- `VALID_ROLES` — `frozenset({"root", "admin", "super_admin", "operator", "half_operator", "user", "guest"})`

## EXCEPTIONS

- `AuthError` — Base authentication exception
- `TokenExpiredError(AuthError)` — JWT has expired
- `TokenInvalidError(AuthError)` — JWT signature or structure is invalid

## ENVIRONMENT

| Variable | Default | Description |
|----------|---------|-------------|
| `LUMINA_JWT_SECRET` | — | HMAC signing key (required for production) |
| `LUMINA_JWT_TTL_MINUTES` | `60` | Token time-to-live in minutes |
| `LUMINA_JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `LUMINA_PASSWORD_HASH_ALGORITHM` | `argon2id` | Password hashing algorithm: `argon2id`, `bcrypt`, or `sha256` |

## NOTES

This module uses zero external dependencies for JWT — implemented using the standard library (`hmac`, `hashlib`, `base64`). Password hashing supports optional external libraries (`argon2-cffi`, `bcrypt`) for production-grade security; install via `pip install project-lumina[passwords]`. When neither is installed, SHA-256 with per-user salt is used as a fallback. Production deployments should evaluate an external IdP.

## ERP Claim Contract (Slice 37)

For non-system actors, Lumina accepts ERP-issued identity context according to:

1. [erp-jwt-claim-contract-v1](../5-standards/erp-jwt-claim-contract-v1.md)
2. [erp-auth-fallback-policy-v1](../5-standards/erp-auth-fallback-policy-v1.md)

### Required ERP Claims

`iss`, `aud`, `sub`, `exp`, `iat`, `jti`, `role`, `organization_id`, `site_id`

### Optional ERP Claims

`domain_roles`, `governed_modules`, `device_id`, `site_role`

### Deterministic Denial Conditions

| Condition | Denial reason |
|----------|---------------|
| Missing required claim | `MISSING_REQUIRED_CLAIM` |
| Invalid issuer | `INVALID_ISSUER` |
| Invalid audience | `INVALID_AUDIENCE` |
| Expired token | `TOKEN_EXPIRED` |
| Invalid temporal claims | `INVALID_TIME_CLAIMS` |
| Malformed claim payload | `MALFORMED_CLAIM` |

### Scenario Coverage (Documentation-Level)

1. Valid token with all required claims and trusted issuer/audience is accepted.
2. Missing required claims (`organization_id`, `site_id`, `role`, `jti`) are denied.
3. Invalid issuer or audience is denied.
4. Expired or invalid time claim relationships are denied.

Runtime middleware implementation of these checks is out of scope for this slice and is delivered in Slice 38.

## SEE ALSO

[permissions(3)](permissions.md), [rbac-spec](../../specs/rbac-spec-v1.md), [erp-jwt-claim-contract-v1](../5-standards/erp-jwt-claim-contract-v1.md), [erp-auth-fallback-policy-v1](../5-standards/erp-auth-fallback-policy-v1.md)

