---
title: "Slice 72 - Vertical Extraction and Configuration Portability Gate"
slice: 72
status: planned
version: 0.1.0
last_updated: 2026-09-24
---

## Purpose

Define the extraction gate proving site profiles, role catalogs, workflow
eligibility, and notification mappings can be exported, imported, and reused
across locations and verticals without framework forks or location-specific
runtime code.

## Scope

- Define export/import pack expectations for site profiles, role catalogs,
  workflow eligibility mappings, and notification-routing configuration.
- Define portability evidence proving multiple sites can share one runtime and
  one neutral code path.
- Define measurable extraction gate criteria tying configuration portability to
  repository-split readiness.
- Define failure conditions when a location would require custom runtime code.

### Upstream Dependencies

- Slice 70 site-variance and role-aware reference scenarios.
- Slice 71 operational overrides, profile versioning, and change governance.

## Out of Scope

- Executing production migrations for customer repositories.
- Implementing new framework features outside portability proof.
- Waiving extraction readiness when site behavior still depends on runtime forks.

## Required Changes

- Document export/import artifact expectations for site and role configuration.
- Document portability gate metrics and pass/fail thresholds for multi-site
  reuse without custom runtime code.
- Document governance evidence required before extraction or replication into
  vertical repositories.
- Document remediation expectations when portability proof fails.

## New/Changed Contracts

- New: `configuration_portability_gate_contract_v1`.
- New: `site_profile_export_import_contract_v1`.
- New: `role_and_notification_mapping_portability_contract_v1`.

## Files Likely Touched

- `docs/roadmap/slices/72-vertical-extraction-and-configuration-portability-gate.md`
- `docs/roadmap/slices/65-pack-extraction-tooling-and-vertical-repository-template.md`
- `docs/roadmap/slices/66-authoring-guides-and-extraction-readiness-closeout.md`
- `model-packs/template/`

## Acceptance Criteria

- Export/import expectations are explicit for site profiles, role catalogs,
  workflow eligibility rules, and notification mappings.
- Portability gate criteria provide measurable proof that multiple sites require
  no custom runtime code.
- Failure conditions and remediation requirements are explicit before extraction
  or reuse is approved.
- Gate outputs are compatible with the framework-to-vertical extraction posture.

## Tests

- Documentation review against extraction-readiness and scenario-governance
  slices.
- Link verification for referenced roadmap slices and template surfaces.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Converts portability claims into auditable extraction gates.
- Prevents business-specific repository split-out while location variance still
  depends on hidden runtime customization.

## Follow-Up Slices

- Future extraction execution slices as needed.
