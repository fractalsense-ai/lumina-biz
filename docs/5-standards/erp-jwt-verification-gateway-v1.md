---
version: 1.0.0
last_updated: 2026-08-05
---

# ERP JWT Verification Gateway V1

**Version:** 1.0.0  
**Status:** Active  
**Last updated:** 2026-08-05

---

## Purpose

Define deterministic runtime verification behavior for ERP-issued JWTs used by Lumina domain and user tracks.

This contract is normative for issuer and audience verification, signature verification, time validation, and replay checks.

---

## Inputs

| Variable | Description |
|----------|-------------|
| `LUMINA_ERP_TRUSTED_ISSUER` | Trusted ERP issuer value for `iss` claim |
| `LUMINA_ERP_EXPECTED_AUDIENCE` | Expected Lumina audience value for `aud` claim |
| `LUMINA_ERP_JWT_SECRET` | HMAC secret for ERP token signature verification |
| `LUMINA_ERP_CLOCK_SKEW_SECONDS` | Allowed clock skew tolerance for temporal validation |

---

## Verification Sequence

1. Parse JWT structure and decode header or payload.
2. Validate required claims from [erp-jwt-claim-contract-v1](erp-jwt-claim-contract-v1.md).
3. Validate `iss` against `LUMINA_ERP_TRUSTED_ISSUER`.
4. Validate `aud` against `LUMINA_ERP_EXPECTED_AUDIENCE`.
5. Verify token signature using `LUMINA_ERP_JWT_SECRET`.
6. Validate temporal bounds (`iat`, `exp`) with bounded skew tolerance.
7. Reject replayed or revoked `jti` values.

A verification failure at any step MUST deny the token.

---

## Canonical Denial Reasons

| Condition | Denial reason |
|-----------|---------------|
| Missing required claim | `MISSING_REQUIRED_CLAIM` |
| Invalid issuer | `INVALID_ISSUER` |
| Invalid audience | `INVALID_AUDIENCE` |
| Signature verification failure | `INVALID_SIGNATURE` |
| Token expired | `TOKEN_EXPIRED` |
| Invalid temporal claims | `INVALID_TIME_CLAIMS` |
| Malformed claim value or type | `MALFORMED_CLAIM` |
| Revoked or replayed token id | `TOKEN_REVOKED` |

---

## Scope Constraints

1. This gateway applies to ERP-governed non-system actors only.
2. It does not grant or expand system admin authority.
3. Admin or system continuity fallback behavior remains a separate control-plane concern.

---

## Out of Scope

This contract does not define:

1. Middleware route wiring for endpoint-level enforcement.
2. Full enterprise IdP federation or OIDC discovery.
3. UI login flow migration.

Those are handled in subsequent Slice 38 implementation PRs.

---

## Related Contracts

1. [erp-jwt-claim-contract-v1](erp-jwt-claim-contract-v1.md)
2. [erp-rbac-mapping-v1](erp-rbac-mapping-v1.md)
3. [auth-endpoint-transition-policy-v1](auth-endpoint-transition-policy-v1.md)
