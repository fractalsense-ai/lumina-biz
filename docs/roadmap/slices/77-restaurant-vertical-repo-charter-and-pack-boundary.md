---
title: "F&B Vertical Repo Charter and Pack Boundary"
slice: 77
status: planned
version: 1.1.0
last_updated: 2026-11-08
---

## Purpose

Define public `lumina-fnb` as the food-and-beverage vertical repository derived from `lumina-biz`. The same public core-fork pattern applies to `lumina-cstore`, `lumina-retail`, and `lumina-auto`; customer-specific repositories are private and downstream of those public verticals.

## Scope

- Define the F&B repo's ownership, module boundary, and release lifecycle.
- Define its pinned `lumina-biz` baseline and upstream update process.
- Identify which shared capabilities remain in `lumina-biz` and which food-and-beverage workflows belong downstream.
- Define the path from vertical release to a private customer solution repository.

## Out of Scope

- Building the F&B runtime or creating a private customer deployment.
- Committing supplier/customer data or credentials.
- Replacing the core with a permanent divergent fork.

## Required Changes

- Document the F&B repository charter and pack boundary.
- Define CI compatibility checks against a supported business-core release.
- Document the same public fork pattern for c-store, dry retail, and auto-care/repair/towing repositories.

## New/Changed Contracts

- `fnb_vertical_repo_charter_v1`
- `vertical_pack_boundary_contract_v1`
- `vertical_core_compatibility_contract_v1`

## Acceptance Criteria

- F&B-specific workflows, schemas, and provider mappings have a clear owner in `lumina-fnb`.
- Shared business capabilities remain upstream in `lumina-biz`.
- The vertical records its supported core range and a tested update path.
- Customer-specific repositories are downstream of vertical releases, not peers of the shared core.

## Tests

- Review a sample repository tree and dependency pin.
- Verify the proposed conformance and upgrade checks.
- Run repo verification and manifest integrity checks.
