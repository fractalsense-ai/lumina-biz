---
title: "Slice 58 - Module Command Surface Contract v1"
slice: 58
status: planned
version: 0.1.0
last_updated: 2026-09-22
---

## Purpose

Define a standardized module command surface for structured operations with deterministic validation, RBAC, audit, and idempotency semantics.

## Scope

- Define structured command envelope and per-module command schema contract.
- Define validation, RBAC, audit, and idempotency requirements for command execution.
- Clarify command-path behavior: structured operation commands may bypass SLM parsing, while freeform command text may still use SLM parsing.
- Define command failure taxonomy and evidence requirements.

### Upstream Dependencies

- Slice 53 module authoring contract.
- Slice 56 turn interpreter contract.
- Slice 57 deterministic pre-LLM routing contract.
- Slice 44 mutation safety and idempotency ledger planning context.

## Out of Scope

- Implementing new command handlers in runtime code.
- Replacing existing global admin command infrastructure.

## Required Changes

- Document command contract v1 and module command declaration requirements.
- Document RBAC/idempotency/audit invariants for command-path execution.
- Document SLM-bypass versus SLM-assisted parsing decision boundaries.

## New/Changed Contracts

- New: `module_command_surface_contract_v1`.
- New: `module_structured_command_enforcement_policy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/58-module-command-surface-contract-v1.md`
- `src/lumina/api/dependencies.py`
- `src/lumina/system_log/commit_guard.py`
- `model-packs/business-ops/modules/`

## Acceptance Criteria

- Structured command envelope and validation requirements are explicit.
- RBAC, audit, and idempotency guarantees are required for command execution.
- SLM bypass policy language is explicit and unambiguous.

## Tests

- Documentation contract review against current auth/audit/idempotency surfaces.
- Link verification for command-path references.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Ensures command-path mutations remain auditable and governed even when SLM parsing is bypassed.
- Reduces risk of undocumented command behavior drift across modules.

## Follow-Up Slices

- Slice 59.
- Slice 63.

