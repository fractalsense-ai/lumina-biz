---
title: "Slice 64 - Multi-Site and Cross-Location Aggregation Contract"
slice: 64
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Define organization/site isolation, cross-site authorization, aggregation, and routing semantics for reusable multi-location vertical behavior.

## Scope

- Define organization/site isolation invariants for read and mutation paths.
- Define cross-site authorization requirements and deny/fallback semantics.
- Define cross-location aggregation request/response contract.
- Define routing semantics for single-site versus cross-site operations.

### Upstream Dependencies

- Slice 26 tenant/site/actor memory contracts.
- Slice 28 semantic thread routing and context forking.
- Slice 63 reference vertical exemplar definition.

## Out of Scope

- Building customer-specific multi-site policies.
- Replacing existing auth framework.

## Required Changes

- Document multi-site authorization and aggregation contract.
- Document routing and context-carrying semantics for cross-location operations.
- Document governance and audit expectations for cross-site access.

## New/Changed Contracts

- New: `multi_site_aggregation_contract_v1`.
- New: `cross_location_authorization_policy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/64-multi-site-and-cross-location-aggregation-contract.md`
- `src/lumina/api/dependencies.py`
- `src/lumina/retrieval/`
- `src/lumina/thread_routing/`

## Acceptance Criteria

- Isolation and cross-site authorization semantics are explicit and deterministic.
- Aggregation contract is explicit for request scope and response provenance.
- Routing semantics align with existing tenant/site context handling slices.

## Tests

- Documentation review against tenant/site/actor and routing surfaces.
- Link verification for referenced runtime directories and prior slices.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Strengthens governance for cross-location access decisions and aggregation evidence.
- Reduces risk of ambiguous site-boundary behavior during vertical extraction.

## Follow-Up Slices

- Slice 65.
- Slice 70.
- Slice 72.
