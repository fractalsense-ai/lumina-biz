---
title: "Slice 62 - ERP Auth Cutover Wiring"
slice: 62
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Plan the wiring of ERP JWT verification into non-system request authentication while preserving Lumina system-track authentication boundaries.

## Scope

- Define target auth-path wiring from ERP JWT gateway to non-system request paths.
- Preserve and explicitly protect system-track auth behavior.
- Reconcile current status and remaining work from Slice 38.
- Define cutover sequencing and rollback considerations for auth path changes.

### Upstream Dependencies

- Slice 38 ERP JWT verification gateway and auth transition.
- Slice 41 ERP program gate and dependency lock.
- Slice 59 workflow contract context for execution-path identity assumptions.

## Out of Scope

- Full production enablement of ERP mutation transport.
- Authorization model redesign unrelated to ERP cutover wiring.

## Required Changes

- Document auth cutover wiring plan and boundaries.
- Document compatibility requirements for system versus non-system tracks.
- Document evidence requirements for safe cutover readiness.

## New/Changed Contracts

- New: `erp_auth_cutover_wiring_plan_v1`.
- New: `system_track_auth_preservation_policy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/62-erp-auth-cutover-wiring.md`
- `src/lumina/api/dependencies.py`
- `src/lumina/api/processing.py`
- `docs/roadmap/slices/38-erp-jwt-verification-gateway-and-auth-transition.md`

## Acceptance Criteria

- Non-system auth cutover path is explicit and references Slice 38 artifacts.
- System-track auth preservation constraints are explicit and testable.
- Cutover readiness evidence requirements are documented without overstating closure.

## Tests

- Documentation review against current auth dependencies and processing pipeline docs.
- Link verification for Slice 38 and runtime auth references.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Supports auditable auth cutover planning while preserving system authority boundaries.
- Reduces risk of accidental auth-surface regressions during ERP transition work.

## Follow-Up Slices

- Slice 63.

