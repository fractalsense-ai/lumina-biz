---
title: "Slice 71 - Operational Overrides, Profile Versioning, and Change Governance"
slice: 71
status: planned
version: 0.1.0
last_updated: 2026-09-24
---

## Purpose

Define governance for effective-dated site overrides and profile changes so
operational exceptions remain visible, reversible, and incapable of silently
changing workflow behavior.

## Scope

- Define effective-dated, site-scoped overrides for emergency closures,
  equipment outages, lease changes, and similar operational exceptions.
- Define site-profile and role-catalog versioning expectations.
- Define approval, rollback, cache-invalidation, and audit requirements for
  override activation and removal.
- Define safeguards that prevent silent workflow/task eligibility or
  notification-routing changes.

### Upstream Dependencies

- Slice 67 site profile and capability declaration contract.
- Slice 68 capability-gated workflow and task eligibility contract.
- Slice 69 role catalog, assignment, and notification routing contract.

## Out of Scope

- Implementing runtime cache layers or admin consoles.
- Replacing broader workflow-state durability work from earlier slices.
- Unbounded emergency powers that bypass audit or rollback evidence.

## Required Changes

- Document effective-dated override semantics and site/profile scoping rules.
- Document versioning, approval, rollback, and invalidation requirements for
  profile-affecting changes.
- Document failure and deny behavior for invalid or conflicting overrides.
- Document audit requirements preventing silent workflow or routing changes.

## New/Changed Contracts

- New: `site_operational_override_contract_v1`.
- New: `site_profile_versioning_contract_v1`.
- New: `profile_change_governance_contract_v1`.
- New: `workflow_change_visibility_policy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/71-operational-overrides-profile-versioning-and-change-governance.md`
- `docs/8-admin/`
- `src/lumina/system_log/`
- `src/lumina/api/processing.py`

## Acceptance Criteria

- Effective-dated override behavior is explicit for closures, outages, lease
  changes, and similar exceptions.
- Versioning, approval, rollback, and cache-invalidation expectations are
  explicit and auditable.
- Invalid or conflicting overrides have deterministic failure behavior.
- The contract explicitly prevents silent workflow/task or notification-routing
  changes.

## Tests

- Documentation review against site-profile, eligibility, and role-routing
  slices.
- Link verification for referenced admin and runtime surfaces.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Makes operational exceptions and reversions reviewable after the fact.
- Reduces outage and lease-change risk by governing emergency configuration
  changes instead of hiding them in code.

## Follow-Up Slices

- Slice 72.
