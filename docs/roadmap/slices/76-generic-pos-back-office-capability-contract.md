---
title: "Slice 76 - Generic POS and Back-Office Capability Contract"
slice: 76
status: planned
version: 1.0.0
last_updated: 2026-11-08
---

## Purpose

Define provider-neutral business capabilities that `lumina-biz` can expose to multiple vertical repositories without becoming a vendor-specific ERP or POS implementation.

## Scope

- Define POS, labor, payroll, accounting, and back-office capability families.
- Define connector mapping and capability discovery boundaries.
- Preserve external systems of record as authoritative for their data domains.
- Define API-only cross-domain access and fallback semantics.

## Out of Scope

- Production connector transports or provider parity implementation.
- Restaurant menu, recipe, or receiving rules.
- Replacing customer systems of record.

## Required Changes

- Document capability names, request/response semantics, and unsupported-operation behavior.
- Define provider mapping and conformance expectations.
- Align capabilities with Tool Token permissions and audit requirements.

## New/Changed Contracts

- `pos_back_office_capability_contract_v1`
- `provider_connector_capability_map_v1`
- `sor_authority_boundary_contract_v1`

## Acceptance Criteria

- Capabilities are vendor-neutral and reusable by distinct verticals.
- Provider-specific behavior is isolated behind connector mappings.
- External systems of record retain authority over their domains.
- Cross-domain operations use target-domain APIs and are auditable.

## Tests

- Review example capability payloads against existing connector contracts.
- Verify permission, unsupported-operation, and fallback cases.
- Run repo verification and manifest integrity checks.
