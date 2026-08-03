---
title: "Slice 33 — ERPNext Reference Connector and Deterministic Fixtures"
slice: 33
status: delivered
version: 0.2.0
last_updated: 2026-08-03
---

## Purpose

Implement ERPNext as the first reference connector that conforms to canonical business-system contracts and capability routing rules.

## Scope

- Implement connector manifest, capability declaration, and operation mappings for ERPNext.
- Implement deterministic fixture mode for ERPNext connector tests and local development.
- Define provider-specific mapping layer from canonical envelopes to ERPNext API/doctypes.
- Define connector-level error normalization into canonical `connector_error` format.

## Out of Scope

- ERPNext-specific fields promoted into canonical schemas.
- Production-grade credential rotation implementation.
- Secondary provider implementation.

## Required Changes

- Add ERPNext connector package under provider-specific module namespace.
- Add mapping specs for first supported capabilities.
- Add fixture scenarios for query and draft-mutation flows.
- Add conformance tests against canonical request/result contracts.

## New/Changed Contracts

- New provider binding contract: `provider=erpnext` mapping profile.
- New connector fixture contract instances for ERPNext scenarios.
- New canonical error mapping set for ERPNext response classes.

## Files Likely Touched

- `src/lumina/**` (connector implementation)
- `tests/test_*connector*erpnext*`
- `docs/1-commands/**` and `docs/7-concepts/**`
- `docs/roadmap/slices/33-erpnext-reference-connector-and-fixtures.md`

## Acceptance Criteria

- ERPNext connector passes canonical conformance tests for supported capabilities.
- Deterministic fixtures cover nominal and failure paths.
- Provider specifics remain isolated to mapping layer.
- No credential-bearing data in fixtures, logs, or prompt payloads.

## Tests

- Canonical contract conformance tests for ERPNext connector.
- Fixture replay tests for each supported operation.
- Negative tests for malformed mappings and unsupported capabilities.

### Implementation Evidence (2026-08-03)

- ERPNext reference connector implementation is complete with deterministic fixture support and canonical request/response mapping.
- Connector routing and capability handling are validated via focused connector, routing, and replay suites.
- Connector outcomes are normalized into canonical error envelopes and routed through shared business-ops replay flows.

Validated command outputs:

- `pytest tests/test_module_routing.py tests/test_business_ops_replay_service.py tests/test_business_ops_pack.py -q` -> `35 passed`
- `pytest tests/test_routes_workflow.py tests/test_business_ops_pack.py tests/test_module_routing.py tests/test_pipeline_fix.py tests/test_business_ops_replay_service.py tests/test_business_ops_e2e_fixture.py -q` -> `60 passed`

Key evidence artifacts:

- `docs/roadmap/slices/33-erpnext-reference-connector-execution-plan.md`
- `tests/test_module_routing.py`
- `tests/test_business_ops_replay_service.py`
- `tests/test_business_ops_pack.py`

## Ledger/Governance Impact

- Connector calls and normalized outcomes are evidence-bearing events.
- Governance authority unchanged; connector only executes routed allowed operations.

## Follow-Up Slices

- Slice 34: secondary provider connector and conformance harness.
- Slice 35: auto-repair MVP over connector abstractions.

## Implementation-Ready PR Description Template

### Title

Slice 33: ERPNext reference connector with deterministic fixture conformance

### PR Scope

- Implement ERPNext connector manifest, capability declarations, and canonical operation mapping.
- Implement deterministic fixture mode for supported query and staged mutation operations.
- Add connector-level ERPNext error normalization into canonical `connector_error` classes.
- Add conformance tests and fixture replay tests for supported operations.

### Acceptance Criteria

- ERPNext connector passes canonical conformance tests for each supported capability.
- Deterministic fixture scenarios cover nominal and failure paths.
- Provider-specific field mapping remains isolated to ERPNext mapping layer.
- No credential-bearing values appear in fixture artifacts, logs, or prompt payloads.

### Test Checklist

- [ ] Canonical contract conformance tests for ERPNext operations.
- [ ] Deterministic fixture replay tests for each supported capability.
- [ ] Negative tests for malformed mapping and unsupported capability routing.
- [ ] Error normalization tests for ERPNext response classes.
- [ ] Secret hygiene checks for fixtures and connector logs.

### Out of Scope Confirmations

- No canonical schema expansion for ERPNext-only fields.
- No production credential rotation system in this slice.
- No secondary provider connector implementation.
