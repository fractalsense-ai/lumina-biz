---
title: "Slice 63 - Neutral Reference Vertical Exemplar Pack"
slice: 63
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Define a neutral, non-customer reference vertical pack that proves framework contracts end-to-end before business-specific repository extraction.

## Scope

- Define a site-operations exemplar pack with at least two modules.
- Require demonstration of multi-site context handling and structured observation capture.
- Require demonstration of workflow DAG execution and staged mutation behavior.
- Require audit evidence outputs aligned with framework governance contracts.

### Upstream Dependencies

- Slice 58 module command surface contract.
- Slice 60 workflow state durability and recovery contract.
- Slice 61 generic connector contract consolidation.
- Slice 62 ERP auth cutover wiring plan.

## Out of Scope

- Customer-specific business logic or proprietary data models.
- Immediate extraction into a standalone repository in this slice.

## Required Changes

- Define reference vertical objectives, module set, and acceptance harness.
- Define required demonstration scenarios for multi-site observations and staged mutation.
- Define minimum audit evidence package required for exemplar completion.

## New/Changed Contracts

- New: `reference_vertical_exemplar_contract_v1`.
- New: `exemplar_acceptance_scenario_matrix_v1`.

## Files Likely Touched

- `docs/roadmap/slices/63-neutral-reference-vertical-exemplar-pack.md`
- `model-packs/business-ops/`
- `src/lumina/api/processing.py`
- `src/lumina/system_log/commit_guard.py`

## Acceptance Criteria

- Reference vertical definition includes at least two modules and required scenarios.
- Scenarios include multi-site context, structured observation capture, DAG execution, and staged mutation.
- Audit evidence requirements are explicit and compatible with existing governance controls.

## Tests

- Documentation review against module/workflow/command and connector contracts.
- Link verification for referenced pack/runtime/audit files.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Provides a reusable proof artifact for framework readiness without coupling to a specific customer vertical.
- Strengthens extraction governance by requiring auditable exemplar evidence before split-out.

## Follow-Up Slices

- Slice 64.
- Slice 65.
- Slice 70.
