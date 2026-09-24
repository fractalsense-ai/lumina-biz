---
title: "Slice 59 - Workflow Definition Contract and DAG Compilation"
slice: 59
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Define declarative domain workflow contracts and compilation into execution DAGs, reusing coding-agent DAG patterns where compatible.

## Scope

- Define module workflow definition schema and lifecycle fields.
- Define workflow-to-DAG compilation contract and deterministic compile outputs.
- Define compatibility and reuse boundaries with `model-packs/coding-agent/` DAG contracts.
- Define compile-time validation and failure taxonomy.

### Upstream Dependencies

- Slice 53 module authoring contract.
- Slice 56 turn interpreter contract.
- Slice 57 deterministic routing contract.
- Existing DAG lineage from Slices 12 and 14.

## Out of Scope

- Full production rollout of durable workflow runtime state.
- New generic orchestration engine rewrite.

## Required Changes

- Document workflow definition contract and compile semantics.
- Document coding-agent DAG reuse strategy and differences for business-domain workflows.
- Document compile validation requirements and governance evidence outputs.

## New/Changed Contracts

- New: `domain_workflow_definition_contract_v1`.
- New: `workflow_dag_compilation_contract_v1`.

## Files Likely Touched

- `docs/roadmap/slices/59-workflow-definition-contract-and-dag-compilation.md`
- `model-packs/coding-agent/`
- `src/lumina/api/processing.py`
- `src/lumina/thread_routing/`

## Acceptance Criteria

- Workflow definition schema and DAG compile outputs are explicit and deterministic.
- Reuse strategy for coding-agent DAG contracts is documented and bounded.
- Compile failure taxonomy and validation evidence expectations are explicit.

## Tests

- Documentation review against existing DAG architecture slices and runtime surfaces.
- Link verification for coding-agent and runtime references.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Creates auditable lineage from declarative workflows to executable DAGs.
- Reduces governance risk from implicit or ad hoc workflow compilation behavior.

## Follow-Up Slices

- Slice 60.
- Slice 62.
- Slice 63.
- Slice 68.
