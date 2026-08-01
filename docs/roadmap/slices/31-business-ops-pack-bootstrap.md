---
title: "Slice 31 — Connector Registry and Capability Routing"
slice: 31
status: delivered
version: 1.0.0
last_updated: 2026-07-31
---

## Purpose

Define deterministic connector registration and capability routing so each site can run one primary connector or multiple active connectors selected by operation capability.

## Scope

- Define connector instance identity and tenancy scoping (`organization_id`, `site_id`, `connector_instance_id`).
- Define routing precedence:
	- operation-level override,
	- capability route,
	- site primary connector,
	- organization default connector,
	- no-route failure.
- Define connector capability negotiation and health status contracts.
- Define idempotency and correlation requirements for mutation operations.

## Out of Scope

- Provider-specific API client implementation.
- Vertical workflow implementation.
- Distributed transaction orchestration across external systems.

## Required Changes

- Add connector registry contract and routing decision contract.
- Add deterministic routing policy fixtures (single primary and multi-connector cases).
- Add connector health and capability validation checks.

## New/Changed Contracts

- New `connector_registry_entry` contract.
- New `capability_route_policy` contract.
- New `connector_resolution_result` contract.
- New operation idempotency key/correlation requirements for connector calls.

## Files Likely Touched

- `docs/7-concepts/*.md`
- `standards/*.json` (new routing/registry contracts)
- `tests/test_*routing*` (new)
- `docs/roadmap/slices/31-business-ops-pack-bootstrap.md`

## Acceptance Criteria

- Connector resolution is deterministic and testable.
- Single-primary and multi-connector routing patterns are both supported.
- Missing-route and unhealthy-connector paths produce structured errors.
- No credential material appears in registry/routing artifacts.

## Tests

- Deterministic routing tests for precedence and fallback.
- Connector capability/health validation tests.
- Negative tests for ambiguous routes and missing idempotency keys.

## Delivery Evidence

- `pytest tests/test_connector_routing.py tests/test_connector_routing_contracts.py tests/test_connector_routing_api.py -q`
  - Result: `21 passed`
- Connector-routing contracts delivered under `standards/` and validated by contract tests.
- Scoped preflight route and transcript-free routing-decision evidence wiring delivered.

## Ledger/Governance Impact

- Connector resolution and routing outcomes become auditable metadata for business-system operations.
- Governance boundaries unchanged; routing does not grant execution authority.

## Follow-Up Slices

- Slice 32: business-ops pack bootstrap.
- Slice 33: ERPNext reference connector and deterministic fixtures.
