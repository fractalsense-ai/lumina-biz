---
title: "Slice 38 — ERP JWT Verification Gateway and Auth Transition"
slice: 38
status: delivered
version: 0.1.4
last_updated: 2026-08-06
---

## Purpose

Implement Lumina runtime verification of ERP-issued JWTs for domain/user tracks and transition auth endpoints away from Lumina-issued domain/user tokens, while preserving Lumina-issued system-track JWTs for developer/admin control plane.

## Scope

- Define verification gateway for ERP-issued JWTs (`iss`, `aud`, signature, expiry, `jti`).
- Define key-discovery and trust model (static keys and/or JWKS with cache + rotation handling).
- Define domain/user middleware transition from Lumina-issued tokens to ERP-issued tokens.
- Define compatibility/deprecation schedule for legacy domain/user login endpoints.
- Keep system-track login and token issuance (`/api/admin/auth/*`) in Lumina.

## Out of Scope

- Removal of system-track Lumina JWT authentication.
- Full enterprise IdP federation beyond ERP issuer(s).
- UI redesign for auth flows.

## Required Changes

- Add gateway verification contract and failure-mode matrix.
- Define middleware routing rules by issuer/scope for domain/user requests.
- Define endpoint deprecation plan for `/api/auth/login` and `/api/domain/auth/login` issuance paths.
- Define observability and audit fields for token verification outcomes.

## New/Changed Contracts

- New contract: `erp_jwt_verification_gateway_v1`
  - Issuer allowlist
  - Audience allowlist
  - Signature verification strategy
  - Clock-skew tolerance
  - Replay handling (`jti` / short TTL policy)
- New contract: `auth_endpoint_transition_policy_v1`
  - Compatibility window
  - Deprecation phases
  - Rollback criteria

## Files Likely Touched

- `src/lumina/api/middleware.py`
- `src/lumina/auth/auth.py`
- `src/lumina/services/auth/routes.py`
- `docs/8-admin/air-gapped-admin-architecture.md`
- `docs/8-admin/secrets-and-runtime-config.md`
- `docs/3-functions/auth.md`
- `docs/roadmap/slices/38-erp-jwt-verification-gateway-and-auth-transition.md`

## Acceptance Criteria

- Domain/user requests can be authenticated with ERP-issued JWTs under explicit issuer/audience rules.
- Verification gateway behavior is deterministic for key-rotation and invalid-token scenarios.
- Legacy Lumina domain/user token issuance has a documented compatibility window and deprecation path.
- Lumina system-track JWT flow remains functional and explicitly isolated.

## Tests

- Verification-path scenarios:
  - Valid ERP token accepted.
  - Invalid signature rejected.
  - Invalid issuer rejected.
  - Invalid audience rejected.
  - Expired token rejected.
  - Missing required claims rejected.
- Rotation/cache scenarios:
  - Rotated key accepted after refresh.
  - Stale key cache triggers bounded refresh and retry policy.
- Transition scenarios:
  - Legacy domain/user token compatibility behavior during migration window.
  - System-track login unaffected.
- Repository integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Token verification outcomes and fallback events are auditable.
- Separation of authority is strengthened: ERP owns domain/user identity truth; Lumina owns policy enforcement plus system control-plane auth.

## Follow-Up Slices

- Slice 39: generic ERP service core with profile-layer variance and local CI fallback execution protocol while hosted CI is unstable.

## Delivery Notes

- 2026-08-05: PR1 started. Added ERP JWT verification gateway and auth transition policy contracts, plus runtime verification primitive and test coverage for deterministic denial semantics.
- 2026-08-05: Policy baseline set to hard cutover for non-system domain/user actor verification in Slice 38 implementation path, while preserving system/admin continuity boundaries.
- 2026-08-06: PR4 closeout added deterministic token-verification observability fields (hashed actor/context identifiers), emitted structured allow/deny gateway observations, and updated standards/admin documentation.

## Implementation-Ready PR Description Template

### Title

Slice 38: ERP JWT verification gateway and domain/user auth transition

### PR Scope

- Add ERP JWT verification gateway contract.
- Define migration/deprecation path for Lumina-issued domain/user tokens.
- Preserve Lumina system-track JWT path.

### Acceptance Criteria

- ERP token verification contract is complete and testable.
- Migration phases and rollback criteria are explicit.
- System-track auth isolation is preserved.

### Test Checklist

- [ ] Invalid token scenario matrix documented and mapped to expected deny behavior.
- [ ] Key-rotation/cache strategy documented with deterministic fallback.
- [ ] Legacy compatibility and final deprecation phases documented.
- [ ] Repo integrity checks pass.

### Out of Scope Confirmations

- No removal of `/api/admin/auth/*` system-track flows.
- No full enterprise IdP migration beyond ERP issuer contract.
