---
title: "Slice 70 - Site-Variance and Role-Aware Reference Scenarios"
slice: 70
status: planned
version: 0.1.0
last_updated: 2026-09-24
---

## Purpose

Define reference scenarios proving that the same neutral domain and module code
produces correct outcomes across materially different site profiles, role
assignments, and notification-routing outcomes.

## Scope

- Define scenario matrix coverage for capability present/absent differences,
  contractual exclusions, and operating-constraint suppression.
- Define role-routing and notification-outcome coverage for multiple site
  staffing patterns.
- Define negative scenarios where no notification is sent because no eligible
  role or capability exists.
- Define scenario evidence showing shared neutral code across all sites.

### Upstream Dependencies

- Slice 68 capability-gated workflow and task eligibility contract.
- Slice 69 role catalog, assignment, and notification routing contract.

## Out of Scope

- Implementing production site profiles or production notification adapters.
- Creating customer-specific SOP content outside the neutral reference pack.
- Replacing broader extraction-readiness evidence from later slices.

## Required Changes

- Document scenario matrix proving the same neutral pack handles materially
  different locations through configuration alone.
- Document role-routing and notification assertions, including negative
  no-notification cases.
- Document evidence requirements demonstrating contractual exclusions suppress
  inapplicable tasks.
- Document provenance requirements linking each scenario to the governing site
  profile and role catalog inputs.

## New/Changed Contracts

- New: `site_variance_reference_scenario_matrix_v1`.
- New: `role_aware_notification_outcome_contract_v1`.

## Files Likely Touched

- `docs/roadmap/slices/70-site-variance-and-role-aware-reference-scenarios.md`
- `model-packs/business-ops/`
- `docs/roadmap/slices/63-neutral-reference-vertical-exemplar-pack.md`
- `docs/roadmap/slices/68-capability-gated-workflow-and-task-eligibility-contract-v1.md`
- `docs/roadmap/slices/69-role-catalog-assignment-and-notification-routing-contract-v1.md`

## Acceptance Criteria

- Scenario matrix covers materially different site profiles using the same
  neutral domain/module code.
- Scenarios cover capability presence/absence, contractual exclusions,
  operating constraints, role routing, and notification outcomes.
- Negative scenarios prove that inapplicable work does not emit tasks or
  notifications.
- Evidence requirements make each scenario outcome reproducible and auditable.

## Tests

- Documentation review against eligibility and notification-routing contracts.
- Link verification for referenced slices and pack directories.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Provides auditable proof that multi-site variance is configuration-driven.
- Creates a durable scenario set for rejecting future location-specific runtime
  forks.

## Follow-Up Slices

- Slice 72.
