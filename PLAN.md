# PLAN.md — Current Execution Plan

_Last updated: 2026-11-06_

## Why This File Changed

The repo was still pointing at an outdated slice sequence. This plan now reflects the current docs-first execution path: the framework boundary has been locked and the next implementation target is the domain pack authoring contract.

## Active Target

Slice 52: Domain Pack Authoring Contract v1

Roadmap source:
- docs/roadmap/slices/51-framework-boundary-lock-and-pack-taxonomy-reconciliation.md
- docs/roadmap/slices/52-domain-pack-authoring-contract-v1.md

Current status:
- Slice 51 established the framework boundary and the package taxonomy baseline.
- Slice 52 is the active execution target and defines the mandatory `pack.yaml` contract for future domain packs.
- The next downstream workstream continues through Slices 53-66 once the pack contract is locked.

## Objective

Define the canonical, schema-backed domain pack authoring contract so every future pack has a consistent identity, governance, routing surface, and compatibility policy before implementation work proceeds.

## Baseline Rule

Execution must preserve the framework boundary established by Slice 51:
- Base framework core remains exactly `system`, `template`, and `coding-agent`.
- `business-ops` remains a seed vertical used for validation and later extraction.
- Future vertical work must extend domain packs and profile/gateway layers without disturbing the base framework boundary.

Roadmap anchor:
- docs/7-concepts/framework-boundary.md
- docs/7-concepts/domain-pack-authoring-contract-v1.md

## Scope

1. Pack taxonomy and contract baseline (Slice 51)
- Confirm the three-pack framework core.
- Reconcile the repository taxonomy to distinguish framework packs from provisional vertical packs.
- Lock shared terminology used by the downstream authoring slices.

2. Domain pack authoring contract (Slice 52)
- Define required and optional `pack.yaml` fields.
- State default module, routing, scope, and governance metadata expectations.
- Define compatibility and versioning semantics for future extraction and portability.
- Document migration expectations for existing packs such as `model-packs/business-ops/pack.yaml`.

3. Downstream follow-through
- Continue into Slice 53 (module authoring contract) only after the pack contract is accepted.
- Keep all implementation work aligned to the docs-first, PR-based workflow.

## Out of Scope

- Creating new runtime loader behavior in this phase.
- Provider-specific connector implementation details.
- Broad module implementation beyond the authoring contracts.

## Acceptance Criteria

- The framework boundary is explicitly documented and stable.
- `pack.yaml` contract fields are defined with required/optional semantics.
- Scope and routing defaults are unambiguous for new domain packs.
- Versioning and compatibility expectations are documented.

## Test Checklist

- [ ] Roadmap and boundary documentation remain consistent with package taxonomy.
- [ ] `pack.yaml` manifest contract is documented in the concept docs and slice doc.
- [ ] Repo integrity checks pass.
- [ ] Manifest/hash integrity checks pass.

## Notes

Historical plans remain in the slice docs under `docs/roadmap/slices/` instead of this top-level plan. This file is the current execution baseline for the active repository workstream.
