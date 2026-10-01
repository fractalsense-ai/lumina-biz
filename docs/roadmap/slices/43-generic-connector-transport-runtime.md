---
title: "Slice 43 - Generic Connector Transport Runtime"
slice: 43
status: planned
version: 0.1.0
last_updated: 2026-08-08
---

## Purpose

Define and implement the provider-agnostic connector transport runtime used by
all ERP adapters, including timeout, retry, correlation, and idempotency-key plumbing.

## Scope

- Implement generic transport interfaces for outbound connector calls.
- Define timeout and retry policy matrix by action class and error class.
- Define correlation ID propagation and tracing expectations.
- Define idempotency key propagation contract for mutation-capable operations.

## Out of Scope

- Provider-specific payload shaping beyond adapter boundaries.
- Production cutover enablement.
- Secondary provider rollout.

## Required Changes

- Add transport runtime layer and policy hooks.
- Add canonical error envelope mapping at transport boundary.
- Add deterministic request metadata propagation requirements.

## New/Changed Contracts

- New: `generic_connector_transport_runtime_v1`.
- New: `connector_transport_retry_policy_v1`.
- Extended: canonical connector error envelope usage for transport failures.

## Files Likely Touched

- `src/lumina/business_ops/connectors/*/execute.py`
- `src/lumina/business_ops/connectors/errors.py`
- `src/lumina/connector_routing/router.py`
- `standards/connector-error-schema-v1.json`
- `docs/roadmap/slices/43-generic-connector-transport-runtime.md`

## Acceptance Criteria

- Generic transport runtime is provider-agnostic and reusable.
- Timeout/retry/correlation behavior is deterministic and test-covered.
- Idempotency key metadata is propagated for mutation classes.

## Tests

- Transport timeout and retry matrix tests.
- Correlation propagation and trace evidence tests.
- Error normalization tests at transport boundary.
- Integrity checks:
  - `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
  - `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Standardizes external call behavior for consistent auditing.
- Reduces provider coupling risk in execution runtime.

## Follow-Up Slices

- Slice 44, Slice 45, Slice 46, Slice 48.

## Implementation-Ready PR Description Template

### Title

Slice 43: generic connector transport runtime

### PR Scope

- Introduce provider-agnostic transport runtime with policy controls.
- Implement deterministic timeout/retry/correlation behavior.

### Acceptance Criteria

- Runtime contracts are explicit and regression-safe.
- Canonical error envelope mapping remains stable.

### Test Checklist

- [ ] Timeout/retry policy tests.
- [ ] Correlation ID propagation tests.
- [ ] Error envelope normalization tests.
- [ ] `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
- [ ] `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

### Out of Scope Confirmations

- [ ] No provider-specific schema promotion into canonical contracts.
