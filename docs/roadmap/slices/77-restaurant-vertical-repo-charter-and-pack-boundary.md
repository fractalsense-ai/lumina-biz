---
title: "Slice 77 - Restaurant Vertical Repo Charter and Pack Boundary"
slice: 77
status: planned
version: 1.0.0
last_updated: 2026-11-08
---

## Purpose

Define `lumina-restaurants` as the first industry repository derived from `lumina-biz`, while preserving the same reusable-core pattern for `lumina-autorepair` and `lumina-cstore`.

## Scope

- Define the restaurant repo's ownership, module boundary, and release lifecycle.
- Define its pinned `lumina-biz` baseline and upstream update process.
- Identify which shared capabilities remain in `lumina-biz` and which restaurant workflows belong downstream.
- Define the path from vertical release to a private customer solution repository.

## Out of Scope

- Building the restaurant runtime or creating a customer deployment.
- Committing supplier/customer data or credentials.
- Replacing the core with a permanent divergent fork.

## Required Changes

- Document the restaurant repository charter and pack boundary.
- Define CI compatibility checks against a supported business-core release.
- Document the same extraction pattern for the later auto-repair and c-store repositories.

## New/Changed Contracts

- `restaurant_vertical_repo_charter_v1`
- `vertical_pack_boundary_contract_v1`
- `vertical_core_compatibility_contract_v1`

## Acceptance Criteria

- Restaurant-specific workflows, schemas, and provider mappings have a clear owner in `lumina-restaurants`.
- Shared business capabilities remain upstream in `lumina-biz`.
- The vertical records its supported core range and a tested update path.
- Customer-specific repositories are downstream of vertical releases, not peers of the shared core.

## Tests

- Review a sample repository tree and dependency pin.
- Verify the proposed conformance and upgrade checks.
- Run repo verification and manifest integrity checks.
