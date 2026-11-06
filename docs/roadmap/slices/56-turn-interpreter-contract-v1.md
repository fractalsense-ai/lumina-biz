---
title: "Slice 56 - Turn Interpreter Contract v1"
slice: 56
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Define a deterministic turn-interpreter contract for module selection, extraction targets, evidence fields, and confidence output semantics.

## Scope

- Define interpreter input envelope fields and required context fields.
- Define extraction target structure (entities, measurements, intents, evidence pointers).
- Define confidence scoring and reason taxonomy expectations.
- Define output contract for module/workflow candidate selection.

### Upstream Dependencies

- Slice 53 module authoring contract.
- Slice 54 glossary/index contract.
- Runtime orchestration surface: `src/lumina/api/processing.py`.

## Out of Scope

- Selecting a specific model family for interpreter execution.
- Full parser implementation changes.

## Required Changes

- Document interpreter markdown contract v1.
- Document confidence and evidence semantics used by downstream routing/workflow stages.
- Document deterministic fallback behavior when interpretation confidence is insufficient.

## New/Changed Contracts

- New: `turn_interpreter_contract_v1`.
- New: `turn_interpreter_evidence_confidence_contract_v1`.

## Files Likely Touched

- `docs/roadmap/slices/56-turn-interpreter-contract-v1.md`
- `model-packs/business-ops/modules/auto-repair/`
- `src/lumina/api/processing.py`
- `src/lumina/core/nlp.py`

## Acceptance Criteria

- Interpreter input/output schemas are explicit and implementation-ready.
- Confidence and evidence fields are defined with deterministic fallback semantics.
- Module/workflow selection outputs are compatible with downstream routing contracts.

## Tests

- Documentation contract review against current processing and NLP pipeline stages.
- Link verification for referenced module/runtime files.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Improves explainability by requiring structured evidence/confidence outputs from interpretation stages.
- Supports governance review of interpreter-driven routing decisions.

## Follow-Up Slices

- Slice 57.
- Slice 58.
- Slice 59.

