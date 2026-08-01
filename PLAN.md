# PLAN.md — Current Execution Plan

_Last updated: 2026-08-01_

## Why This File Changed

The previous content in this file was a historical, slice-specific planning artifact (including Hermes prototype notes) and is no longer the right top-level plan for current delivery.

This file now tracks the active implementation target and handoff details.

## Active Target

Slice 33: ERPNext Reference Connector and Deterministic Fixtures

Roadmap source:
- docs/roadmap/slices/33-erpnext-reference-connector-and-fixtures.md

Current status:
- Slice 32 is delivered and validated.
- Slice 33 is active and is the current execution focus.

## Objective

Deliver the first provider-specific reference connector (`erpnext`) that conforms to Lumina canonical business-system contracts and deterministic routing behavior.

## Scope

1. Connector core
- Add ERPNext connector package under `src/lumina/**`.
- Implement connector manifest/capability declaration.
- Implement canonical operation dispatch.
- Implement canonical-to-ERPNext mapping layer.

2. Deterministic fixture mode
- Add fixture-backed execution mode for local tests and CI.
- Cover nominal query flows and staged mutation flows.
- Cover deterministic provider failure responses.

3. Error normalization + conformance
- Normalize ERPNext failures to canonical `connector_error` shapes.
- Add conformance tests per supported capability.
- Add negative tests for unsupported capabilities and malformed mappings.

4. Documentation
- Add command/concept docs for running connector fixtures.
- Document provider isolation boundary (canonical vs ERPNext specifics).
- Update roadmap evidence after green test pass.

## Out of Scope

- Canonical schema expansion for ERPNext-only fields.
- Production credential rotation implementation.
- Secondary provider implementation.

## Acceptance Criteria

- ERPNext connector passes canonical conformance tests for supported capabilities.
- Deterministic fixtures cover nominal and failure paths.
- Provider-specific logic stays isolated to mapping/adapter layer.
- No credential-bearing data in fixtures, logs, or prompt payloads.

## Test Checklist

- [ ] `tests/test_*connector*erpnext*` pass.
- [ ] Fixture replay tests pass per supported operation.
- [ ] Negative tests pass for malformed mappings and unsupported capabilities.
- [ ] Error normalization tests pass for ERPNext response classes.
- [ ] Secret hygiene checks pass for fixture/log artifacts.

## Implementation-Ready PR Description Template

### Title

Slice 33: ERPNext reference connector with deterministic fixture conformance

### PR Scope

- Implement ERPNext connector capability declarations and canonical mappings.
- Add deterministic fixture mode and replay scenarios.
- Add conformance + error-normalization test coverage.
- Update operator and concept docs for connector boundaries.

### Acceptance Criteria

- Supported capabilities pass canonical conformance tests.
- Fixture mode reproduces nominal and failure paths deterministically.
- Provider specifics remain isolated from canonical contracts.
- No credential-bearing data in fixtures/logs/prompts.

### Test Checklist

- [ ] Conformance tests for supported operations.
- [ ] Fixture replay tests for nominal and error cases.
- [ ] Unsupported capability / malformed mapping negatives.
- [ ] Error normalization contract tests.
- [ ] Secret hygiene verification.

### Out of Scope Confirmations

- No production credential rotation in this slice.
- No secondary provider connector in this slice.
- No ERPNext-specific field promotion into canonical schemas.

## Notes

If historical plans are needed for audit, they should live in slice docs under `docs/roadmap/slices/` rather than this top-level execution plan.
