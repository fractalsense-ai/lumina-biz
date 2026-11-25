---
title: "Slice 42 - ERP Trust Runtime and Live Actor-Liveness Adapter"
slice: 42
status: in-progress
version: 0.5.1
last_updated: 2026-11-18
---

## Purpose

Harden runtime trust boundaries for ERP-authenticated actors and define the live
SoR liveness adapter contract used by protected API flows.

## Scope

- Define runtime integration contract for ERP trust validation.
- Define live actor-liveness adapter semantics and deterministic deny-closed behavior.
- Define observability fields for allow/deny outcomes with pseudonymous identifiers.
- Preserve system-track isolation and existing admin auth boundaries.

## Gate Status (From Slice 41)

- Runtime implementation is blocked until Slice 40 nodes N1, N2, and N3 are
  closed with explicit closure evidence.
- This slice may proceed with documentation hardening, test-planning, and
  contract refinement while gate conditions remain open.

## Out of Scope

- Live ERP business operation execution.
- Connector transport implementation.
- Multi-provider parity rollout.

## Required Changes

- Add trust runtime hardening requirements and failure matrix.
- Add live liveness adapter contract and fallback rules.
- Add governance references for auth-path observability.

## Contract Definition Packet (Pre-Implementation)

### Adapter Interface

- `erp_actor_liveness_adapter_v1` must define:
  - actor identity inputs (organization, site, actor claims, token metadata).
  - a structured `ActorLivenessResult` with strict boolean `allow`, nullable `deny_reason`, and a lowercase identifier-format non-PII `evidence_code`.
  - accepted deny reasons limited to `actor_inactive_in_sor`, `actor_liveness_unavailable`, and `actor_liveness_malformed`; allow results use `actor_active_in_sor`.
  - timeout semantics and explicit unavailable behavior.

### Deterministic Failure Matrix

| Condition | Expected Outcome | Reason Code |
|---|---|---|
| Adapter returns `true` | allow | `actor_active_in_sor` |
| Adapter returns `false` | deny | `actor_inactive_in_sor` |
| Adapter unavailable/timeout | deny | `actor_liveness_unavailable` |
| Adapter malformed/non-bool outcome | deny | `actor_liveness_malformed` |

### Observability Requirements

- Emit pseudonymous actor-liveness observation fields only.
- Include deterministic event type and reason taxonomy.
- Do not emit raw token contents, PII, or ERP credential material.

## New/Changed Contracts

- New: `erp_trust_runtime_hardening_v1`.
- New: `erp_actor_liveness_adapter_v1`.
- Extended: `actor_liveness_enforcement_v1` mapping to ERP runtime adapter.

## Files Likely Touched

- `src/lumina/api/dependencies.py`
- `src/lumina/auth/auth.py`
- `src/lumina/auth/operating_context.py`
- `docs/5-standards/erp-jwt-verification-gateway-v1.md`
- `docs/roadmap/slices/42-erp-trust-runtime-and-live-actor-liveness-adapter.md`

## Acceptance Criteria

- Live liveness adapter contract is explicit and deterministic.
- Deny-closed behavior remains mandatory on verifier unavailability or malformed responses.
- Auth-path observability remains pseudonymous and deterministic.
- Slice remains docs/test-planning only while Slice 41 gate conditions are open.

## Tests

- Verifier returns true/false and malformed values matrix.
- Adapter unavailable and timeout denial behavior matrix.
- Existing protected-route regression coverage.
- Gate policy validation:
  - no runtime implementation files modified while N1-N3 remain unresolved.
- Integrity checks:
  - `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
  - `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Strengthens trust boundary evidence for actor validity checks.
- Prevents silent auth degradation during ERP outages.

## Runtime Progress

- The injected actor-liveness verifier now consumes a structured `ActorLivenessResult`, validates the strict boolean/reason/evidence fields, and distinguishes malformed results (`actor_liveness_malformed`) from unavailable or timeout failures (`actor_liveness_unavailable`); both remain deny-closed and emit pseudonymous observations.
- Local persistence verification and injected adapters use the same result contract; failure-matrix coverage passes (11 tests).
- `ERPNextActorLivenessAdapter` checks the read-only Frappe `User.enabled` field through the generic transport seam, with expected organization/site binding and an injected authorization-header provider. Fixture tests cover active, disabled, missing, malformed, unavailable, scope mismatch, HTTPX URL-log suppression, credential-provider failure, and public package export (12 passed).
- API lifespan composition is opt-in and requires `LUMINA_ERP_ACTOR_LIVENESS_BASE_URL`, `LUMINA_ERP_ACTOR_LIVENESS_ORGANIZATION_ID`, `LUMINA_ERP_ACTOR_LIVENESS_SITE_ID`, `LUMINA_ERP_ACTOR_LIVENESS_API_KEY`, and `LUMINA_ERP_ACTOR_LIVENESS_API_SECRET`. Incomplete configuration fails startup; credentials are read from the process environment at each check, and the owned HTTP client is closed at shutdown. This config binds one ERP organization/site per API process; other scopes are denied before network access.
- Runtime-composition tests cover opt-in behavior, partial configuration, credential rotation, scope enforcement, and lifespan cleanup (4 passed). No live ERP instance was available or contacted; production acceptance still requires approved live-instance verification. No credentials or endpoint values are committed, and Slice 42 remains in progress.

## Follow-Up Slices

- Slice 43, Slice 45, Slice 47, Slice 48.

## Pre-Implementation PR Checklist (Gate-Safe)

- [ ] Contract packet sections complete and internally consistent.
- [ ] Deterministic failure matrix includes timeout/unavailable/malformed paths.
- [ ] Observability requirements preserve pseudonymity constraints.
- [ ] No runtime code changes included while Slice 41 gate remains closed.

## Implementation-Ready PR Description Template

### Title

Slice 42: trust runtime hardening and live actor-liveness adapter contract

### PR Scope

- Define and prepare the ERP liveness adapter contract path.
- Enforce deterministic deny-closed requirements at specification level.
- Limit this slice increment to docs/test-planning while hard gate is closed.

### Acceptance Criteria

- Liveness adapter contract is test-covered and deterministic.
- Non-bool/invalid verifier outputs are denied closed.
- Runtime implementation remains blocked unless N1-N3 closure evidence is linked.

### Test Checklist

- [ ] Positive and negative liveness adapter path tests.
- [ ] Unavailable/timeout fallback denial tests.
- [ ] Protected-route regression tests.
- [ ] `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
- [ ] `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

### Out of Scope Confirmations

- [ ] No ERP business operation transport implementation.
- [ ] No runtime adapter implementation until Slice 41 hard gate is released.
