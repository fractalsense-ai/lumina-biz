---
title: "Slice 51 - Framework Boundary Lock and Pack Taxonomy Reconciliation"
slice: 51
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Lock the reusable framework boundary and reconcile pack taxonomy/documentation so downstream contract slices can be authored against one unambiguous target shape.

## Scope

- Reassert the framework core as exactly `system`, `coding-agent`, and `template`.
- Classify `business-ops` as a seed vertical pack intended for later extraction.
- Reconcile stale roadmap/architecture wording that conflicts with the current repository layout.
- Define terminology for framework packs, vertical packs, and modules used by Slices 52-66.

### Upstream Dependencies

- Slice 39 direction lock (`39-generic-erp-service-core-and-vertical-profile-layer.md`).
- Slice 40 coherence enforcement framing (`40-architecture-coherence-enforcement-hardening.md`).
- Slice 41 ERP program governance gate (`41-erp-integration-program-charter-and-dependency-lock.md`).

## Out of Scope

- Runtime code movement, pack extraction, or module implementation changes.
- Introducing new vertical packs in this slice.

## Required Changes

- Add boundary-lock documentation language for framework versus vertical packs.
- Add taxonomy definitions for pack classes and module placement.
- Reconcile roadmap references that still imply non-existent framework packs.

## New/Changed Contracts

- New: `framework_pack_taxonomy_lock_v1`.
- New: `seed_vertical_classification_policy_v1`.

## Files Likely Touched

- `docs/roadmap/README.md`
- `docs/7-concepts/framework-boundary.md`
- `model-packs/README.md`
- `docs/roadmap/slices/51-framework-boundary-lock-and-pack-taxonomy-reconciliation.md`

## Acceptance Criteria

- Framework boundary is explicitly documented as three core packs.
- `business-ops` is explicitly documented as seed vertical scaffolding.
- Terminology is consistent across roadmap boundary references.

## Tests

- Documentation consistency review across roadmap and framework-boundary docs.
- Link verification for referenced roadmap slices and boundary docs.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Reduces architectural drift by setting an auditable taxonomy baseline before additional contract work.
- Clarifies ownership boundaries for future framework versus vertical changes.

## Follow-Up Slices

- Slice 52.

