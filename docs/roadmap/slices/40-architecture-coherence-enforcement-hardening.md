---
title: "Slice 40 — Architecture Coherence Enforcement Hardening"
slice: 40
status: planned
version: 0.1.0
last_updated: 2026-08-06
---

## Purpose

Close high-risk architecture enforcement gaps so runtime behavior matches the
intended Lumina framework shape for authority boundaries, memory constraints,
and cross-domain execution safety.

## Scope

- Implement explicit tool-token boundary enforcement in runtime invocation flow.
- Enforce institutional-memory ingest guardrails for prohibited payload classes.
- Enforce pipeline ordering controls for auth -> NLP -> semantic routing -> PPA.
- Enforce API-only cross-domain execution boundaries.
- Extend daemon paths to audit-commit coverage parity with API paths.
- Add optional active SoR actor-liveness verification with deterministic fallback.

## Out of Scope

- Broad feature expansion for ERP provider completeness.
- Rewriting core orchestration architecture.
- Replacing existing Slice 39 functional direction lock.

## Required Changes

- Add/extend runtime guards in auth, processing, retrieval, and daemon surfaces.
- Add deterministic deny/degrade taxonomy per guard family.
- Add observability for guard activation outcomes using pseudonymous fields.
- Add targeted positive and negative tests for each DAG node closure.

## New/Changed Contracts

- New enforcement contract: `tool_token_boundary_enforcement_v1`.
- New ingestion contract: `institutional_memory_ingest_guardrails_v1`.
- New ordering contract: `pipeline_order_enforcement_v1`.
- New boundary contract: `cross_domain_api_only_enforcement_v1`.
- Extended audit contract: daemon parity requirements over system-log commitment.

## Files Likely Touched

- `src/lumina/api/dependencies.py`
- `src/lumina/api/processing.py`
- `src/lumina/retrieval/institutional.py`
- `src/lumina/daemon/task_adapter.py`
- `src/lumina/daemon/cross_domain.py`
- `src/lumina/orchestrator/system_log_writer.py`
- `tests/test_*`
- `docs/roadmap/architecture-coherence-gap-register.md`

## Acceptance Criteria

- All DAG nodes N1 through N6 are implemented with explicit guards.
- Every guard has deterministic positive and negative tests.
- Observability events prove guard behavior without plaintext sensitive values.
- Cross-domain direct state access outside API pathways is rejected.
- No regression of Slice 39 functional direction-lock guarantees.

## Tests

- Node-level guard tests for N1 through N6.
- End-to-end boundary tests for cross-domain and daemon flows.
- Repo integrity checks:
  - `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
  - `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`
- Local CI fallback verification sequence per Slice 39 protocol.

## Ledger/Governance Impact

- Tightens authority boundaries and memory governance from policy to enforced runtime guarantees.
- Improves auditability by ensuring parity guardrails across API and daemon execution paths.

## Follow-Up Slices

- Subsequent vertical or runtime slices can build on the hardened boundary model
  without re-opening core governance controls.

## Implementation-Ready PR Description Template

### Title

Slice 40: architecture coherence enforcement hardening

### PR Scope

- Implement one or more DAG nodes from N1 to N6 with explicit contracts and tests.
- Add guard observability evidence and failure taxonomy updates.

### Acceptance Criteria

- Target node guards are enforceable, deterministic, and tested.
- No unauthorized tool or boundary bypass behavior remains for targeted nodes.
- Repo and manifest integrity checks pass.

### Test Checklist

- [ ] Targeted node tests (positive + negative).
- [ ] `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
- [ ] `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`
- [ ] Local CI fallback evidence attached.

### Out of Scope Confirmations

- No unrelated feature expansion.
- No weakening of existing zero-trust boundary guarantees.
