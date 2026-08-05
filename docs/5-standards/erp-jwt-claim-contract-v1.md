---
version: 1.0.0
last_updated: 2026-08-05
---

# ERP JWT Claim Contract V1

**Version:** 1.0.0  
**Status:** Active  
**Last updated:** 2026-08-05

---

## Purpose

Define the canonical ERP-issued JWT claim schema that Lumina accepts for non-system actor authorization context.

This contract is normative for claim shape and validation semantics. Runtime verification middleware implementation is deferred to Slice 38.

---

## Required Claims

Every accepted ERP-issued actor token MUST include all fields below:

| Claim | Type | Rule |
|-------|------|------|
| `iss` | string | MUST match configured trusted ERP issuer |
| `aud` | string | MUST match configured Lumina audience |
| `sub` | string | Non-empty actor identifier |
| `exp` | integer | Expiry timestamp; token MUST be unexpired |
| `iat` | integer | Issued-at timestamp |
| `jti` | string | Unique token identifier for replay traceability |
| `role` | string | ERP role value used for authorization mapping |
| `organization_id` | string | Non-empty tenant organization scope |
| `site_id` | string | Non-empty site scope within organization |

## Optional Claims

Optional claims may be present and consumed by policy/mapping layers:

| Claim | Type | Description |
|-------|------|-------------|
| `domain_roles` | array or object | Domain-scoped role hints |
| `governed_modules` | array | Module-scoped boundaries when applicable |
| `device_id` | string | Device context identifier |
| `site_role` | string | Site-specific role hint |

---

## Validation Rules

1. Missing any required claim MUST result in denial.
2. `iss` mismatch MUST result in denial.
3. `aud` mismatch MUST result in denial.
4. Expired tokens MUST result in denial.
5. Invalid temporal relationships (`iat` after `exp`) MUST result in denial.
6. Malformed claim types (for required claims) MUST result in denial.

---

## Canonical Denial Reasons

Use deterministic denial reason identifiers for consistency across audit surfaces:

| Condition | Denial reason |
|-----------|---------------|
| Missing required claim | `MISSING_REQUIRED_CLAIM` |
| Invalid issuer | `INVALID_ISSUER` |
| Invalid audience | `INVALID_AUDIENCE` |
| Token expired | `TOKEN_EXPIRED` |
| Invalid time claims | `INVALID_TIME_CLAIMS` |
| Malformed claim value/type | `MALFORMED_CLAIM` |

---

## Scenario Matrix (Documentation-Level)

| Scenario | Expected result |
|----------|-----------------|
| All required claims valid, trusted issuer/audience, valid timestamps | Accept |
| Missing `organization_id` | Deny (`MISSING_REQUIRED_CLAIM`) |
| Missing `site_id` | Deny (`MISSING_REQUIRED_CLAIM`) |
| Missing `role` or `jti` | Deny (`MISSING_REQUIRED_CLAIM`) |
| `iss` mismatch | Deny (`INVALID_ISSUER`) |
| `aud` mismatch | Deny (`INVALID_AUDIENCE`) |
| `exp` in the past | Deny (`TOKEN_EXPIRED`) |
| `iat` later than `exp` | Deny (`INVALID_TIME_CLAIMS`) |

---

## Out of Scope

This contract does not define:

1. Signature verification implementation details.
2. Key retrieval and JWKS cache internals.
3. Endpoint-level middleware behavior.

Those are implemented in Slice 38 using this contract unchanged.

---

## Related Contracts

1. [erp-identity-authority-v1](erp-identity-authority-v1.md)
2. [erp-auth-fallback-policy-v1](erp-auth-fallback-policy-v1.md)
3. [auth(3)](../3-functions/auth.md)
