---
title: "Slice 57 - Deterministic Pre-LLM Domain-to-Module Routing"
slice: 57
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Formalize deterministic pre-LLM domain/module routing, including degraded-mode telemetry, to align execution behavior with architecture coherence requirements.

## Scope

- Define deterministic routing order and tie-break rules before any LLM call.
- Define degraded-mode triggers and telemetry expectations when deterministic routing cannot complete.
- Define alignment requirements with existing processing pipeline order.
- Define routing-output handoff contract for workflow compilation.

### Upstream Dependencies

- Slice 55 knowledge-index rebuild policy.
- Slice 56 turn interpreter contract.
- Architecture coherence gap G3/N3 in `docs/roadmap/architecture-coherence-gap-register.md`.

## Out of Scope

- Major NLP model changes.
- Full workflow execution implementation.

## Required Changes

- Document pre-LLM routing contract and decision tree.
- Document degraded-mode observation contract and deny/degrade taxonomy.
- Reconcile roadmap wording with N3 pipeline-order enforcement requirements.

## New/Changed Contracts

- New: `pre_llm_domain_module_routing_contract_v1`.
- New: `routing_degraded_mode_telemetry_contract_v1`.

## Files Likely Touched

- `docs/roadmap/slices/57-deterministic-pre-llm-domain-to-module-routing.md`
- `src/lumina/core/nlp.py`
- `src/lumina/api/processing.py`
- `docs/roadmap/architecture-coherence-gap-register.md`

## Acceptance Criteria

- Deterministic routing steps are explicit and independent of LLM availability.
- Degraded-mode signals and telemetry outputs are explicitly documented.
- N3 reconciliation language is explicit and does not overstate closure.

## Tests

- Documentation review against processing pipeline ordering surfaces.
- Link verification for coherence-register and runtime references.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Makes routing decisions auditable even during model degradation.
- Supports governance evidence for order-enforced routing behavior.

## Follow-Up Slices

- Slice 58.
- Slice 59.

