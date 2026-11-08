---
title: "Slice 53 - Module Authoring Contract v1"
slice: 53
status: delivered
version: 0.3.0
last_updated: 2026-11-08
---

## Purpose

Define the required and optional authoring contract for modules so each module is independently reviewable, reusable, and structurally compatible with the domain pack boundary established by Slice 52.

## Scope

- Define the canonical module artifact set and minimum required files
- Define naming and path conventions for module directories and sidecar files
- Define metadata expectations for `module-config.yaml` and operational defaults
- Define compatibility and migration expectations for module reuse across packs
- Define the relationship between the domain pack contract and the module-level contract

### Upstream Dependencies

- Slice 52 domain pack authoring contract
- Existing module examples in `model-packs/business-ops/modules/` and `model-packs/template/modules/`
- Framework boundary and taxonomy lock from Slice 51

## Out of Scope

- Building new modules or workflows in this phase
- Runtime execution-engine behavior changes
- Broad provider-specific implementation details beyond authoring conventions

## Required Changes

- Document the required module artifact matrix with required versus optional status
- Define module directory conventions and the canonical file layout
- Define module-level metadata fields and local defaults
- Define compatibility expectations for module evolution and pack extraction
- Create the concept-level authoring guide consumed by future pack authors

## New/Changed Contracts

- New: `module_authoring_contract_v1`
- New: `module_artifact_presence_policy_v1`
- New: `module_directory_layout_v1`

## Files Likely Touched

- `docs/roadmap/slices/53-module-authoring-contract-v1.md`
- `docs/7-concepts/module-authoring-contract-v1.md`
- `docs/7-concepts/README.md`
- `model-packs/template/modules/example-module/module-config.yaml`
- `model-packs/business-ops/modules/auto-repair/module-config.yaml`

## Core Contract

A module is the bounded behavior unit inside a domain pack. It is not a pack by itself and must never declare framework-level authority. The parent pack defines the outer identity and routing surface; the module defines its runtime state, default task behavior, and local operational defaults.

### Required module surface

Every module should include a deterministic runtime surface:

- `module-config.yaml` with the canonical module metadata and local defaults
- `domain-physics.yaml` and compiled `domain-physics.json`
- a stable module directory path under `model-packs/<domain>/modules/<module>/`
- optional but expected tool, workflow, glossary, and prompt assets when the module needs them

### Required config fields

The repository already uses a stable pattern for module-side config. A valid module config should declare the fields below when applicable:

- `module_id` — stable module identity for routing and provenance
- `module_path` — repository-relative path to the module directory
- `domain_physics_path` — the runtime physics file for the module
- `domain_system_prompt_path` — module-specific persona or domain prompt when used
- `turn_interpretation_prompt_path` — schema or instruction set for turn interpretation
- `local_only` — `true` for governance/admin-style modules that must not call external providers
- `initial_module_state` — seed state for new module sessions
- `default_task_spec` — canonical default task shape for the module
- `domain_step_params` — local operational thresholds and constraints
- `turn_input_defaults` — fallback values used when the turn parser omits fields

The repository's working examples already follow this pattern in `coding-agent` and `template` modules, and the contract should preserve those conventions.

### Required path conventions

- module directories are nested under the parent pack directory and named in lowercase hyphenated form
- the runtime config path resolves to a real file in the repository
- module-level defaults are local to the module and must not leak into the pack-level contract
- module authors should prefer repository-relative paths over loose or implicit runtime path resolution

## Acceptance Criteria

- Module authoring contract clearly distinguishes pack-level and module-level responsibilities
- Required and optional module artifacts are explicitly listed
- Naming/path conventions are explicit and deterministic
- Module compatibility expectations are defined for reuse and extraction
- The contract is consistent with the template and business-ops example modules

## Tests

- Documentation-to-repository structure cross-check for module artifact examples
- Link verification for referenced module files
- Validation check against current module config patterns in the repository
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Creates a stable, auditable module contract for new pack authors
- Prevents drift between pack-level taxonomy and module-level implementation
- Establishes a clean boundary for future extraction and vertical portability work

## Follow-Up Slices

- Slice 54.
- Slice 56.
- Slice 58.
- Slice 59.
- Slice 67.
