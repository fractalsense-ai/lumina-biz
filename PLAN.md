# PLAN.md — Current Execution Plan

_Last updated: 2026-08-03_

## Why This File Changed

The previous content in this file was a historical, slice-specific planning artifact (including Hermes prototype notes) and is no longer the right top-level plan for current delivery.

This file now tracks the active implementation target and handoff details.

## Active Target

Slice 37: ERP Identity Authority and Claim Contract

Roadmap source:
- docs/roadmap/slices/37-erp-identity-authority-and-claim-contract.md
- docs/roadmap/slices/38-erp-jwt-verification-gateway-and-auth-transition.md

Current status:
- Slice 35 and docs decontamination cleanup are complete.
- Slice 37 is active and defines ERP as SSOT for domain/user identity.
- Slice 38 is planned and defines runtime verification and endpoint transition.

## Objective

Establish ERP as the single source of truth (SSOT) for domain/user identity and membership context, while preserving a Lumina-owned JWT track for system/developer control-plane access (`root`, `super_admin`).

## Generic ERP Core Guardrail

Execution must preserve a reusable generic ERP service core where service-like verticals (for example towing and retail-delivery) remain profile/presentation variants over the same canonical workflow and action graph.

Direction lock:
- Prefer profile-layer and mapping-layer extension before any core workflow divergence.
- Keep provider-specific behavior isolated in connector mapping adapters or bounded customization hooks.
- Do not introduce vertical-specific forks in core runtime semantics without an explicit roadmap pivot.

Roadmap anchor:
- docs/roadmap/slices/39-generic-erp-service-core-and-vertical-profile-layer.md

## Scope

1. Identity authority and claim contract (Slice 37)
- Define ERP ownership for domain/user identity lifecycle and organization/site assignment truth.
- Define canonical ERP JWT claim requirements (`iss`, `aud`, `sub`, `exp`, `iat`, `jti`, `role`, `organization_id`, `site_id`).
- Define role and context claim mapping into Lumina runtime authorization.

2. Verification gateway and transition model (Slice 38)
- Define verification strategy for ERP-issued JWTs (issuer/audience/signature/time claims).
- Define key rotation handling (static keys and/or JWKS cache behavior).
- Define compatibility and deprecation stages for Lumina-issued domain/user tokens.

3. System-track preservation
- Keep Lumina-issued system-track JWTs for control-plane operations.
- Preserve `/api/admin/auth/*` as the bounded system/developer path.

4. Operational safeguards
- Define break-glass fallback posture as time-bounded and auditable.
- Define denial behavior for invalid/missing claims.

## Out of Scope

- Full removal of system-track Lumina JWT in this phase.
- Full enterprise IdP federation beyond ERP-issued token contract.
- Immediate hard-cut deletion of all legacy domain/user auth endpoints in Slice 37.

## Acceptance Criteria

- ERP is explicitly documented as SSOT for domain/user identity and membership context.
- Canonical claim contract and verification constraints are unambiguous.
- System-track Lumina JWT path remains explicitly preserved and isolated.
- Migration/deprecation phases for domain/user token issuance are explicit and reversible.

## Test Checklist

- [ ] Contract validation scenarios documented for issuer, audience, required claims, expiry, and invalid signature.
- [ ] Transition scenarios documented for compatibility window and deprecation behavior.
- [ ] System-track auth preservation explicitly verified in docs/contracts.
- [ ] `python -m lumina.systools.verify_repo` passes.
- [ ] `python -m lumina.systools.manifest_integrity check` passes.

## Implementation-Ready PR Description Template (Slice 37)

### Title

Slice 37: ERP identity authority and canonical claim contract

### PR Scope

- Define ERP as SSOT for domain/user identities.
- Define canonical JWT claim contract and validation constraints.
- Preserve Lumina system-track JWT path for control-plane operations.

### Acceptance Criteria

- Claim contract is explicit and internally consistent with RBAC/auth docs.
- Invalid/missing-claim deny behavior is documented.
- Dependency boundaries into Slice 38 are explicit.

### Test Checklist

- [ ] Issuer/audience/claim/expiry scenario matrix documented.
- [ ] Fallback governance behavior documented and bounded.
- [ ] Repo and manifest integrity checks pass.

### Out of Scope Confirmations

- No middleware rewiring in Slice 37.
- No removal of system-track auth endpoints.

## Implementation-Ready PR Description Template (Slice 38)

### Title

Slice 38: ERP JWT verification gateway and domain/user auth transition

### PR Scope

- Define runtime verification gateway for ERP-issued JWTs.
- Define compatibility/deprecation path for Lumina-issued domain/user tokens.
- Preserve system-track Lumina JWT control-plane behavior.

### Acceptance Criteria

- Verification and key-rotation behavior is deterministic and documented.
- Transition/rollback path is explicit.
- System-track preservation is explicit.

### Test Checklist

- [ ] Invalid-token scenario matrix documented.
- [ ] Rotation/cache and fallback behavior documented.
- [ ] Compatibility and deprecation stages documented.
- [ ] Repo and manifest integrity checks pass.

### Out of Scope Confirmations

- No `/api/admin/auth/*` removal in this slice.
- No non-ERP IdP migration in this slice.

## Notes

If historical plans are needed for audit, they should live in slice docs under `docs/roadmap/slices/` rather than this top-level execution plan.
