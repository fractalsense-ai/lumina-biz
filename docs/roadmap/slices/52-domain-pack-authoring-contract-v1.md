---
title: "Slice 52 - Domain Pack Authoring Contract v1"
slice: 52
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Define a versioned, schema-backed domain pack contract so all future vertical packs are authored with consistent identity, governance, and routing defaults.

## Scope

- Define `pack.yaml` required and optional fields (identity, version, owner, vertical type).
- Define allowed modules/connectors declarations and default routing metadata.
- Define organization/site scope declarations and inheritance rules.
- Define contract versioning and compatibility policy.

### Upstream Dependencies

- Slice 51 taxonomy lock.
- Slice 39 generic core/profile direction lock.
- Slice 41 governance gate context for ERP-coupled fields.

## Out of Scope

- Runtime loader implementation changes.
- Provider-specific connector implementation details.

## Required Changes

- Author domain-pack schema contract documentation.
- Define contract validation expectations and failure taxonomy.
- Define migration notes for existing `model-packs/business-ops/pack.yaml`.

## New/Changed Contracts

- New: `domain_pack_authoring_contract_v1`.
- New: `pack_manifest_version_compatibility_policy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/52-domain-pack-authoring-contract-v1.md`
- `model-packs/README.md`
- `docs/7-concepts/framework-boundary.md`
- `src/lumina/core/runtime_loader.py`

## Acceptance Criteria

- `pack.yaml` v1 contract fields are explicitly documented with required/optional status.
- Scope and routing-default semantics are unambiguous.
- Versioning/compatibility expectations are explicit for future extraction tooling.

## Tests

- Documentation contract review against existing pack manifests.
- Link verification for referenced runtime loader and concept docs.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Establishes auditable ownership and change control for domain pack manifests.
- Creates a stable contract surface for pack extraction and cross-repo portability.

## Follow-Up Slices

- Slice 53.
- Slice 67.
- Slice 61.
