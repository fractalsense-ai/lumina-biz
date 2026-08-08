---
title: "Slice 49 - Secondary Provider Adapter Parity"
slice: 49
status: planned
version: 0.1.0
last_updated: 2026-08-08
---

## Purpose

Implement a secondary ERP provider adapter over the generic core and prove
cross-provider parity for canonical operations and error semantics.

## Scope

- Implement secondary provider adapter using existing generic transport/runtime.
- Prove parity for canonical operation classes and error normalization.
- Validate profile-layer variance remains configuration-driven.
- Preserve canonical contracts without provider-specific schema drift.

## Out of Scope

- Full governance closeout and program sunset criteria.
- Additional provider beyond secondary parity target.

## Required Changes

- Add secondary provider adapter and mapping layer.
- Add parity matrix and conformance evidence requirements.
- Add regression guarantees for canonical contract stability.

## New/Changed Contracts

- New: `secondary_provider_adapter_parity_v1`.
- New: `cross_provider_conformance_evidence_v1`.
- Extended: canonical operation parity expectations across providers.

## Files Likely Touched

- `src/lumina/business_ops/connectors/*`
- `src/lumina/business_ops/connectors/conformance.py`
- `tests/test_connector_*`
- `docs/roadmap/slices/49-secondary-provider-adapter-parity.md`

## Acceptance Criteria

- Secondary provider adapter passes canonical conformance suite.
- Cross-provider parity matrix is explicit and test-covered.
- No provider-specific drift in canonical schemas.

## Tests

- Cross-provider conformance matrix tests.
- Canonical envelope parity tests.
- Provider-specific mapping regression tests.
- Integrity checks:
  - `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
  - `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Proves generic-core strategy beyond single-provider implementation.
- Strengthens portability and vendor-risk posture.

## Follow-Up Slices

- Slice 50.

## Implementation-Ready PR Description Template

### Title

Slice 49: secondary provider adapter parity

### PR Scope

- Add secondary provider adapter over generic core.
- Add cross-provider parity and conformance evidence.

### Acceptance Criteria

- Canonical operation parity is proven across two providers.
- Canonical schema stability is preserved.

### Test Checklist

- [ ] Cross-provider conformance tests.
- [ ] Canonical envelope parity tests.
- [ ] Mapping regression tests.
- [ ] `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
- [ ] `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

### Out of Scope Confirmations

- [ ] No tertiary provider rollout in this slice.
