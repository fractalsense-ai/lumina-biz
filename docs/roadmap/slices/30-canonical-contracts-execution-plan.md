---
title: "Slice 30 Execution Plan - Canonical Business-System Contracts"
slice: 30
status: planned
version: 0.1.0
last_updated: 2026-07-24
source_overview: docs/roadmap/slices/30-erpnext-adapter-foundation-and-fixtures.md
---

## Objective

Execute Slice 30 now that Slice 29 is complete by defining provider-neutral contracts, capability taxonomy, and deterministic fixtures that all future connectors must satisfy.

## Exit Criteria (Slice Completion)

- Canonical contract schemas are present under `standards/` and validate deterministically.
- Capability taxonomy is documented and versioned for the first business-ops surface.
- Positive and negative fixture scenarios exist for all action classes.
- No schema permits credential-bearing fields in operation payloads, fixture content, telemetry, or memory artifacts.
- CI/local schema tests pass without regressions.

## Work Plan

### Phase 1 - Contract Inventory and Naming Freeze

1. Confirm canonical contract IDs, filenames, and schema versions.
2. Define stable naming convention for all business-system schema files.
3. Create a short contract matrix mapping each schema to owner, purpose, and validator test.

Deliverables:
- Contract matrix section in this doc.
- Agreed file naming map for `standards/`.

### Phase 2 - Canonical Schema Authoring

1. Add new provider-neutral schemas:
   - `external_system_reference`
   - `business_system_connector_manifest`
   - `business_operation_request`
   - `business_operation_result`
   - `business_system_event`
   - `connector_error`
   - `connector_fixture_scenario`
2. Add shared enum/type definitions for:
   - Action classes: `query`, `create_draft`, `update_draft`, `request_commit`, `request_cancel`, `sync_event`
   - Capability namespaces for the first business-ops surface.
3. Add explicit schema constraints disallowing credentials in operation/fixture fields.

Deliverables:
- New JSON schema files in `standards/`.
- Versioned metadata fields and deterministic required properties.

### Phase 3 - Capability Taxonomy and Conformance Notes

1. Document capability taxonomy for:
   - `party/customer`
   - `catalog/item`
   - `inventory`
   - `sales/pos`
   - `purchasing`
   - `service/work-order`
   - `scheduling`
   - `timekeeping`
   - `accounting/invoice`
2. Define capability-to-action compatibility table.
3. Add conformance notes for future connector implementations.

Deliverables:
- Updated docs under `docs/7-concepts/`.
- Capability/action conformance table.

### Phase 4 - Fixture Scenarios and Validation Harness

1. Add deterministic fixture scenarios per action class and selected capabilities.
2. Add positive and negative fixtures for each canonical schema.
3. Add test harness validating fixtures against schemas.
4. Add backward-compat checks to ensure no breakage in existing standards tests.

Deliverables:
- New/updated tests under `tests/`.
- Deterministic fixture assets and validation tests.

### Phase 5 - Governance and Security Gate

1. Verify no credential-bearing fields exist in any canonical contract.
2. Verify error contracts preserve safe diagnostics without secret leakage.
3. Add explicit governance notes linking envelope usage to policy authority boundaries.

Deliverables:
- Security assertions in tests.
- Governance notes in docs.

## Proposed File Targets

- `standards/business-operation-request-schema-v1.json`
- `standards/business-operation-result-schema-v1.json`
- `standards/business-system-event-schema-v1.json`
- `standards/business-system-connector-manifest-schema-v1.json`
- `standards/external-system-reference-schema-v1.json`
- `standards/connector-error-schema-v1.json`
- `standards/connector-fixture-scenario-schema-v1.json`
- `tests/test_business_system_contract_schemas.py`
- `tests/test_business_system_fixture_validation.py`
- `docs/7-concepts/business-system-contracts.md` (new or updated)

## Risk Register

1. Schema overfitting to one provider implementation.
   - Mitigation: block vendor-specific required fields and enforce canonical-only required properties.
2. Hidden credential fields introduced through free-form metadata.
   - Mitigation: denylist checks and explicit schema restrictions on secret-like keys.
3. Future connector ambiguity in capability routing.
   - Mitigation: strict capability/action compatibility table and conformance tests.

## Implementation-Ready PR Description Template

### Title

Slice 30: Canonical business-system contracts, capability taxonomy, and fixtures

### Scope

- Add provider-neutral canonical schemas for business-system operation envelopes, events, references, connector manifest, fixture scenarios, and connector errors.
- Add capability taxonomy and conformance documentation for initial business-ops namespaces.
- Add deterministic positive/negative fixture validation tests and backward-compat checks.

### Acceptance Criteria

- Canonical schemas support provider-independent workflows with no required vendor fields.
- Action classes are represented consistently across request/result/event contracts.
- Capability taxonomy is explicit, versioned, and documented.
- No credential-bearing field is present in canonical schemas or fixtures.
- Deterministic schema/fixture tests pass in CI and local runs.

### Test Checklist

- [ ] Run schema validation tests for all new canonical contracts.
- [ ] Run positive fixture tests for all action classes.
- [ ] Run negative fixture tests for malformed/forbidden payloads.
- [ ] Run security checks proving no credential-bearing fields are accepted.
- [ ] Run backward-compat standards tests and verify no regressions.

### Out of Scope Confirmations

- No provider-specific client implementation.
- No live external connectivity.
- No runtime connector registry/routing behavior.

## Suggested Execution Order

1. Land schema files and shared enums.
2. Land capability taxonomy doc updates.
3. Land fixture assets and schema tests.
4. Land governance/security assertions.
5. Run full relevant test suite and finalize PR evidence.
