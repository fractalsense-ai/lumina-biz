---
title: "Slice 60 - Workflow State Durability and Recovery"
slice: 60
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Define durable workflow state and recovery requirements to replace or supersede process-local workflow context/draft handling.

## Scope

- Define durable workflow state contract (scope keys, checkpoints, replay semantics).
- Define crash/restart recovery behavior and operator-visible recovery evidence.
- Define compatibility boundaries with existing process-local contexts/drafts.
- Define staged migration strategy from process-local to durable workflow state.

### Upstream Dependencies

- Slice 59 workflow definition and DAG compilation contract.
- Existing execution persistence lineage in Slice 16.

## Out of Scope

- Full data-store implementation for durable workflow state.
- Retrofitting every legacy workflow in this slice.

## Required Changes

- Document durable-state contract and required recovery invariants.
- Document migration and fallback policy from process-local context.
- Document failure taxonomy for partial, conflicted, and stale recovery state.

## New/Changed Contracts

- New: `workflow_state_durability_contract_v1`.
- New: `workflow_recovery_semantics_contract_v1`.

## Files Likely Touched

- `docs/roadmap/slices/60-workflow-state-durability-and-recovery.md`
- `src/lumina/api/processing.py`
- `src/lumina/thread_routing/`
- `docs/8-admin/`

## Acceptance Criteria

- Durable state contract defines scope keys, checkpoints, and replay expectations.
- Recovery behavior and failure taxonomy are explicit and deterministic.
- Migration policy from process-local context is documented and bounded.

## Tests

- Documentation review against existing workflow persistence and routing surfaces.
- Link verification for runtime/admin references.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Improves operational auditability by preserving workflow lifecycle evidence across restarts.
- Reduces mutation-risk from unrecoverable in-memory workflow state.

## Follow-Up Slices

- Slice 63.
- Slice 71.
