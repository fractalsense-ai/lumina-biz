---
title: "Slice 34 — Secondary Provider Connector and Conformance Harness"
slice: 34
status: delivered
version: 0.2.0
last_updated: 2026-08-03
---

## Purpose

Prove provider neutrality by implementing a second business-system connector and validating both connectors against the same canonical conformance harness.

## Scope

- Select one secondary provider (e.g., Odoo, Zoho, QuickBooks, or equivalent) and implement minimal capability subset.
- Build reusable connector conformance harness that executes provider-agnostic test suites.
- Validate route selection behavior when both connectors are active.
- Document provider feature gaps and fallback behavior.

## Out of Scope

- Full feature parity across providers.
- Cross-provider transactional consistency guarantees.
- Production onboarding UX.

## Required Changes

- Add secondary provider connector mapping and capability declarations.
- Add shared conformance harness and reusable fixtures.
- Add route policy tests covering primary and capability-based connector selection.
- Add docs describing connector onboarding and conformance expectations.

## New/Changed Contracts

- New provider binding profile for selected secondary provider.
- New `connector_conformance_result` contract for reporting pass/fail by capability.
- Extended fixture catalog with provider-agnostic expected outcomes.

## Files Likely Touched

- `src/lumina/**` (secondary connector + harness)
- `tests/test_*connector*conformance*`
- `docs/7-concepts/**`
- `docs/roadmap/slices/34-secondary-provider-connector-and-conformance-harness.md`

## Acceptance Criteria

- Both connectors pass shared conformance tests for declared capabilities.
- Route policy works for single-primary and capability-selected paths.
- Canonical contracts remain unchanged by provider-specific differences.
- Unsupported operations fail with structured, deterministic errors.

## Tests

- Shared conformance suite executed against each connector.
- Routing tests across single/multi connector configurations.
- Negative tests for unsupported capabilities and mapping failures.

### Implementation Evidence (2026-08-03)

- Secondary provider conformance harness is implemented and exercised through cross-provider replay scenarios.
- Route selection behavior and cross-module handoff mutation parity are validated against deterministic fixture expectations.
- Portability checks demonstrate identical workflow sequencing and packet-level expectations across conformant connectors.

Validated command outputs:

- `pytest tests/test_business_ops_replay_service.py tests/test_business_ops_e2e_fixture.py -q` -> `5 passed`
- `pytest tests/test_routes_workflow.py tests/test_business_ops_pack.py tests/test_module_routing.py tests/test_pipeline_fix.py tests/test_business_ops_replay_service.py tests/test_business_ops_e2e_fixture.py -q` -> `60 passed`
- `.\.venv\Scripts\python.exe scripts/run_business_ops_replay.py --fixture examples/business-ops-auto-repair-cross-provider-fixture.json --out data/staging/business-ops-cross-provider-report.json` -> report written successfully

Key evidence artifacts:

- `examples/business-ops-auto-repair-cross-provider-fixture.json`
- `data/staging/business-ops-cross-provider-report.json`
- `tests/test_business_ops_e2e_fixture.py`
- `tests/test_business_ops_replay_service.py`

## Ledger/Governance Impact

- Conformance results become auditable evidence for connector readiness.
- Governance posture remains stable across provider selection.

## Follow-Up Slices

- Slice 35: auto-repair MVP over connector abstractions.
- Slice 36: single-box deployment and operational hardening.
