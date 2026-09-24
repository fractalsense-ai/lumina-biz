---
title: "Slice 61 - Generic Connector Contract Consolidation"
slice: 61
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Consolidate generic connector contracts so domain packs remain provider-neutral while provider-specific mappings stay isolated.

## Scope

- Define provider-neutral connector contract boundaries for domain packs/modules.
- Define mapping-layer isolation rules for provider-specific adaptation.
- Reconcile connector contract direction with existing ERP roadmap slices.
- Define connector selection defaults and fallback governance semantics.

### Upstream Dependencies

- Slice 52 domain pack authoring contract.
- Slice 39 generic core/profile direction lock.
- Slices 43-50 ERP connector execution roadmap context.

## Out of Scope

- Implementing new live connector transports.
- Provider parity execution.

## Required Changes

- Document unified connector contract and mapping-boundary policy.
- Document compatibility expectations for ERPNext and future providers.
- Document governance requirements for connector capability declarations in pack manifests.

## New/Changed Contracts

- New: `generic_connector_contract_consolidation_v1`.
- New: `provider_mapping_isolation_policy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/61-generic-connector-contract-consolidation.md`
- `src/lumina/connector_routing/router.py`
- `docs/7-concepts/domain-adapter-pattern.md`
- `model-packs/business-ops/`

## Acceptance Criteria

- Provider-neutral versus provider-specific boundary is explicit.
- Contract language is consistent with Slice 39 direction lock and Slices 43-50.
- Pack-level connector declarations required by Slice 52 are compatible with this contract.

## Tests

- Documentation review against existing connector-routing and adapter-pattern docs.
- Link verification for referenced roadmap and runtime files.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Reduces vendor lock-in risk by enforcing provider-neutral domain contracts.
- Improves auditability of connector-boundary decisions and mapping ownership.

## Follow-Up Slices

- Slice 63.

