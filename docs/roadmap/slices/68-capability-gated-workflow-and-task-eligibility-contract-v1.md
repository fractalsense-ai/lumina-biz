---
title: "Slice 68 - Capability-Gated Workflow and Task Eligibility Contract v1"
slice: 68
status: planned
version: 0.1.0
last_updated: 2026-09-24
---

## Purpose

Define deterministic workflow and task eligibility rules so site capabilities,
exclusions, lease restrictions, and operating predicates decide what can run at
each location without hardcoded per-site logic.

## Scope

- Define required capabilities, exclusions, lease/vendor restrictions, and
  operating predicates on workflows and tasks.
- Define deterministic eligibility evaluation inputs and outputs.
- Define suppression-reason taxonomy for workflows/tasks that do not apply at a
  site.
- Define provenance expectations for compiled eligibility decisions.

### Upstream Dependencies

- Slice 59 workflow definition contract and DAG compilation.
- Slice 67 site profile and capability declaration contract.

## Out of Scope

- Rewriting the workflow execution engine.
- Building site-specific task templates in runtime code.
- Human scheduling or labor-optimization logic outside eligibility evaluation.

## Required Changes

- Document workflow/task fields for required capabilities, exclusions,
  restrictions, and operating predicates.
- Document deterministic evaluation order and suppression-reason outputs.
- Document compile-time and runtime validation expectations for ineligible or
  conflicting workflows.
- Document evidence requirements proving inapplicable tasks are suppressed
  rather than silently emitted.

## New/Changed Contracts

- New: `workflow_eligibility_contract_v1`.
- New: `task_eligibility_evaluation_contract_v1`.
- New: `workflow_suppression_reason_taxonomy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/68-capability-gated-workflow-and-task-eligibility-contract-v1.md`
- `src/lumina/api/processing.py`
- `src/lumina/thread_routing/`
- `model-packs/business-ops/`

## Acceptance Criteria

- Workflow/task eligibility fields are explicit and compatible with Slice 59
  workflow contracts.
- Evaluation semantics are deterministic for capability presence/absence,
  exclusions, lease restrictions, and operating predicates.
- Suppression reasons are explicit, auditable, and suitable for scenario
  testing.
- The contract prevents inapplicable tasks from being generated for a site.

## Tests

- Documentation review against workflow-definition and site-profile contracts.
- Link verification for referenced workflow and runtime surfaces.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Makes task-generation eligibility auditable and explainable per site.
- Prevents silent policy drift where tasks appear or disappear without
  deterministic reasons.

## Follow-Up Slices

- Slice 70.
- Slice 71.
- Slice 72.
