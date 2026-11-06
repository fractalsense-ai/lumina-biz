# PLAN.md — Current Execution Plan

_Last updated: 2026-11-06_

## Why This File Changed

The repo was still pointing at an outdated slice sequence. This plan now reflects the current docs-first execution path: the framework boundary has been locked and the next implementation target is the domain pack authoring contract.

## Active Target

Slice 53: Module Authoring Contract v1

Roadmap source:
- docs/roadmap/slices/52-domain-pack-authoring-contract-v1.md
- docs/roadmap/slices/53-module-authoring-contract-v1.md

Current status:
- Slice 51 established the framework boundary and the package taxonomy baseline.
- Slice 52 is delivered and locks the domain-pack authoring contract for future vertical packs.
- Slice 53 is now the active execution target and defines the module artifact contract that sits beneath the domain pack layer.
- The downstream workstream continues through Slices 54-66 once the module contract is locked.

## Objective

Define the canonical, schema-backed module authoring contract so each module is independently authored, reviewed, and reused across domain packs without drifting from the framework shape.

## Baseline Rule

Execution must preserve the framework boundary and pack contract established by Slices 51 and 52:
- Base framework core remains exactly `system`, `template`, and `coding-agent`.
- `business-ops` remains a seed vertical used for validation and later extraction.
- Domain packs remain the top-level packaging boundary; modules live beneath them and must follow a consistent artifact structure.

Roadmap anchor:
- docs/7-concepts/framework-boundary.md
- docs/7-concepts/domain-pack-authoring-contract-v1.md
- docs/7-concepts/module-authoring-contract-v1.md

## Scope

1. Domain pack lock baseline (Slices 51-52)
- Confirm the three-pack framework core.
- Keep the repository taxonomy aligned to the framework and pack boundary.
- Preserve the domain-pack authoring contract as the authoritative pack metadata layer.

2. Module authoring contract (Slice 53)
- Define required and optional module artifacts.
- State naming/path conventions and ownership metadata expectations.
- Define compatibility and migration expectations for future module extraction and reuse.
- Document how modules fit beneath a domain pack without violating the framework boundary.

3. Downstream follow-through
- Continue into Slice 54 (module glossary/index contract) once the module contract is accepted.
- Keep all implementation work aligned to the docs-first, PR-based workflow.

## Out of Scope

- Building new modules or workflows in this phase.
- Runtime execution-engine behavior changes.
- Broad provider-specific implementation beyond the contract layer.

## Acceptance Criteria

- The framework boundary remains explicitly documented and stable.
- Module artifact contract fields are defined with required/optional semantics.
- Naming, path, and ownership conventions are unambiguous for module authoring.
- Compatibility and migration expectations are documented for future module reuse.

## Test Checklist

- [ ] Roadmap and boundary documentation remain consistent with the pack and module taxonomy.
- [ ] Module contract is documented in the concept docs and slice doc.
- [ ] Repo integrity checks pass.
- [ ] Manifest/hash integrity checks pass.

## Notes

Historical plans remain in the slice docs under `docs/roadmap/slices/` instead of this top-level plan. This file is the current execution baseline for the active repository workstream.
