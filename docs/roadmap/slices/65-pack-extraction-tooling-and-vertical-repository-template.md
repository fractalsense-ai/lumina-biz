---
title: "Slice 65 - Pack Extraction Tooling and Vertical Repository Template"
slice: 65
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Define the tooling and procedure for extracting a domain pack into a standalone business repository that consumes Lumina framework dependencies.

## Scope

- Define extraction workflow, invariants, and required preconditions.
- Define vertical repository template structure and dependency model on framework core.
- Define contract/test/doc artifacts required in extracted vertical repositories.
- Define backward-compatibility and update-channel expectations after extraction.

### Upstream Dependencies

- Slice 52 domain pack authoring contract.
- Slice 63 reference vertical exemplar pack.
- Slice 64 multi-site and cross-location aggregation contract.

## Out of Scope

- Executing extraction for multiple real customer repositories.
- Designing business-specific proprietary module content.

## Required Changes

- Document extraction command/procedure and governance checkpoints.
- Document repository template contract for extracted verticals.
- Document framework-to-vertical dependency and version pinning strategy.

## New/Changed Contracts

- New: `pack_extraction_process_contract_v1`.
- New: `vertical_repository_template_contract_v1`.

## Files Likely Touched

- `docs/roadmap/slices/65-pack-extraction-tooling-and-vertical-repository-template.md`
- `model-packs/template/`
- `docs/7-concepts/framework-boundary.md`
- `scripts/`

## Acceptance Criteria

- Extraction process and preconditions are explicit and reproducible.
- Vertical repository template expectations are explicit and scoped.
- Framework dependency and versioning strategy for extracted repos is documented.

## Tests

- Documentation walkthrough of extraction steps using reference vertical assumptions.
- Link verification for template/framework references.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Creates auditable extraction procedures before business-specific repo split-out.
- Clarifies ownership boundaries between framework and extracted vertical repositories.

## Follow-Up Slices

- Slice 66.
- Slice 72.
