---
title: "Slice 69 - Role Catalog, Assignment, and Notification Routing Contract v1"
slice: 69
status: planned
version: 0.1.0
last_updated: 2026-09-24
---

## Purpose

Define a declarative role and notification-routing contract so work assignment,
escalation, and notification delivery follow configurable site roles rather than
hardcoded actor lists.

## Scope

- Define role/title catalog fields, skills, site assignments, shifts, and
  availability metadata.
- Define actor-vs-role separation for task eligibility and notification
  targeting.
- Define notification targets, escalation chains, fallback behavior, and
  configurable notification-adapter mappings.
- Define audit and privacy expectations for assignment and notification routing.

### Upstream Dependencies

- Slice 67 site profile and capability declaration contract.
- Slice 26 tenant/site/actor memory contracts.

## Out of Scope

- Implementing live messaging integrations.
- Building workforce-management or payroll features.
- Hardcoded per-site recipient lists or title-specific runtime branches.

## Required Changes

- Document role catalog, assignment, and availability contract fields.
- Document assignment evaluation boundaries between actor identity and role
  eligibility.
- Document notification routing, escalation, fallback, and adapter-configuration
  expectations.
- Document privacy, audit, and retention expectations for routing metadata.

## New/Changed Contracts

- New: `site_role_catalog_contract_v1`.
- New: `task_assignment_routing_contract_v1`.
- New: `notification_routing_contract_v1`.
- New: `notification_adapter_configuration_contract_v1`.

## Files Likely Touched

- `docs/roadmap/slices/69-role-catalog-assignment-and-notification-routing-contract-v1.md`
- `docs/7-concepts/framework-boundary.md`
- `src/lumina/thread_routing/`
- `src/lumina/system_log/`

## Acceptance Criteria

- Role/title catalog fields, site assignment semantics, and availability
  metadata are explicit and versioned.
- Task-routing rules distinguish role-based assignment from individual actor
  identity.
- Notification routing, escalation, and fallback semantics are declarative and
  configurable.
- Audit/privacy expectations are explicit for notification-target resolution and
  delivery evidence.

## Tests

- Documentation review against tenant/site/actor scoping and routing surfaces.
- Link verification for referenced concept and runtime directories.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Creates auditable assignment and notification decisions for operational work.
- Prevents private routing data and escalation logic from being hidden in
  per-location code.

## Follow-Up Slices

- Slice 70.
- Slice 71.
- Slice 72.
