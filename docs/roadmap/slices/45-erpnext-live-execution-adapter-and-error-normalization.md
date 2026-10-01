---
title: "Slice 45 - ERPNext Live Execution Adapter and Error Normalization"
slice: 45
status: planned
version: 0.1.0
last_updated: 2026-08-08
---

## Purpose

Implement the first live ERP provider adapter (ERPNext) over the generic runtime
while preserving canonical request/result contracts and deterministic error normalization.

## Scope

- Implement live ERPNext execution path behind canonical operation envelopes.
- Map provider errors into canonical error schema with preserved provider diagnostics.
- Preserve actor scope and policy controls from prior slices.
- Keep adapter boundaries thin and provider-specific.

## Out of Scope

- Secondary provider rollout.
- Production full cutover enablement.
- Long-term SLO governance closeout.

## Required Changes

- Add ERPNext live adapter runtime wiring.
- Add provider-to-canonical error mapping matrix.
- Add adapter observability fields for correlation and policy auditing.

## New/Changed Contracts

- New: `erpnext_live_execution_adapter_v1`.
- New: `provider_error_normalization_mapping_v1`.
- Extended: canonical connector operation contract conformance for live mode.

## Files Likely Touched

- `src/lumina/business_ops/connectors/erpnext/execute.py`
- `src/lumina/business_ops/connectors/erpnext/errors.py`
- `src/lumina/business_ops/connectors/erpnext/mapping.py`
- `src/lumina/api/routes/*connector*`
- `docs/roadmap/slices/45-erpnext-live-execution-adapter-and-error-normalization.md`

## Acceptance Criteria

- ERPNext live execution path is operational under canonical contracts.
- Provider errors map deterministically to canonical schema.
- Scope and policy enforcement remains intact in live path.

## Tests

- Live adapter positive/negative flow tests.
- Provider error mapping matrix tests.
- Actor scope and policy regression tests on connector routes.
- Integrity checks:
  - `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
  - `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Enables first live provider execution with preserved audit semantics.
- Maintains canonical envelope governance despite provider specifics.

## Follow-Up Slices

- Slice 46, Slice 48, Slice 49.

## Implementation-Ready PR Description Template

### Title

Slice 45: ERPNext live execution adapter and canonical error normalization

### PR Scope

- Implement ERPNext live execution adapter over generic runtime.
- Add deterministic provider-to-canonical error normalization.

### Acceptance Criteria

- Live adapter path is functional and contract-compliant.
- Error normalization matrix passes with deterministic outputs.

### Test Checklist

- [ ] ERPNext live adapter integration tests.
- [ ] Error mapping matrix tests.
- [ ] Connector scope and policy regression tests.
- [ ] `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
- [ ] `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

### Out of Scope Confirmations

- [ ] No secondary provider implementation in this slice.
