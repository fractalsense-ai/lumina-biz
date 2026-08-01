---
title: "Slice 33 Execution Plan - ERPNext Reference Connector and Deterministic Fixtures"
slice: 33
status: active
version: 0.1.0
last_updated: 2026-08-01
source_overview: docs/roadmap/slices/33-erpnext-reference-connector-and-fixtures.md
---

## Objective

Deliver the first provider-specific reference connector for ERPNext while preserving canonical contracts, deterministic execution, and governance boundaries introduced in slices 30 and 31.

## Exit Criteria (Slice Completion)

- ERPNext connector manifest/capability declarations align with canonical connector manifest schema.
- Canonical operation requests map deterministically to ERPNext provider payloads.
- Deterministic fixture mode supports nominal and failure paths for supported capabilities.
- ERPNext provider errors normalize to canonical connector_error payloads.
- Conformance and replay tests are green.
- No credential-bearing data is introduced in fixtures, logs, or prompt payloads.

## Work Plan

### Phase 1 - Connector Scaffold and Contract Binding

1. Add ERPNext connector package under `src/lumina/business_ops/connectors/erpnext/`.
2. Add provider manifest builder aligned to canonical connector-manifest schema.
3. Freeze supported capability/action matrix for this slice.

Deliverables:
- ERPNext connector module scaffold.
- Deterministic manifest builder and capability matrix tests.

### Phase 2 - Canonical Mapping Layer

1. Implement canonical request to ERPNext payload mapping helpers.
2. Keep provider-specific field transforms isolated from canonical request/result structures.
3. Fail deterministically for unsupported capability/action pairs.

Deliverables:
- Mapping helpers for initial operations.
- Negative tests for unsupported mappings.

### Phase 3 - Deterministic Fixture Execution

1. Implement fixture runner for local and CI execution without network calls.
2. Support scenario IDs and structured fixture-missing errors.
3. Produce canonical operation result shapes.

Deliverables:
- Deterministic fixture runner.
- Fixture replay tests for nominal and failure paths.

### Phase 4 - Error Normalization

1. Normalize provider errors to canonical connector_error shape.
2. Map common ERPNext failures (validation/auth/rate-limit/upstream) to stable codes.
3. Preserve retryability semantics deterministically.

Deliverables:
- Error normalization helper.
- Error contract tests.

### Phase 5 - Integration and Evidence

1. Add focused test suite for manifest, mapping, fixtures, and normalization.
2. Run targeted connector tests and slice 32 safety regression checks.
3. Update slice 33 roadmap status and evidence once implementation is complete.

Deliverables:
- Green test evidence.
- Roadmap status update with completion notes.

## Initial File Targets

- `src/lumina/business_ops/connectors/erpnext/__init__.py`
- `src/lumina/business_ops/connectors/erpnext/manifest.py`
- `src/lumina/business_ops/connectors/erpnext/mapping.py`
- `src/lumina/business_ops/connectors/erpnext/fixtures.py`
- `src/lumina/business_ops/connectors/erpnext/errors.py`
- `tests/test_connector_erpnext_manifest.py`
- `tests/test_connector_erpnext_fixtures.py`

## Validation Commands

- `python -m pytest tests/test_connector_erpnext_manifest.py tests/test_connector_erpnext_fixtures.py -q`
- `python -m pytest tests/test_business_ops_pack.py -q`
- `lumina-manifest-regen`
- `lumina-integrity-check`

## Out of Scope Confirmations

- No production credential rotation.
- No secondary provider implementation.
- No canonical schema expansion for provider-only fields.
