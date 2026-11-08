---
title: "Slice 73 - Business Core and Vertical Repository Boundary"
slice: 73
status: active
version: 1.0.0
last_updated: 2026-11-08
---

## Purpose

Define `lumina-biz` as the reusable business core and establish the boundary between shared business behavior, industry vertical repositories, and customer-specific solutions.

## Scope

- Distinguish the generic `lumina-framework` engine from the business core in `lumina-biz`.
- Keep shared business capabilities in `lumina-biz` while isolating restaurant, auto-repair, and convenience-store behavior in their respective repositories.
- Define the vertical fork/upstream and customer-private-repository lifecycle.
- Inventory legacy vertical-specific assumptions and assign an owner: core, vertical, or customer.

## Out of Scope

- Removing shared business capabilities from `lumina-biz` merely because they currently reside in a business-ops pack.
- Implementing vertical runtime features or creating customer repositories.
- Provider-specific production deployment.

## Required Changes

- Add the normative business repository topology concept.
- Align the active plan and roadmap with the engine/core/vertical/customer layers.
- Record vertical contamination and ownership decisions with follow-up work.

## New/Changed Contracts

- `business_repository_topology_v1`
- `business_core_boundary_v1`
- `vertical_upstream_compatibility_policy_v1`
- `customer_solution_repository_policy_v1`

## Acceptance Criteria

- `lumina-framework`, `lumina-biz`, vertical repositories, and private customer solutions have distinct responsibilities.
- Shared business capabilities are retained in `lumina-biz`; vertical-specific behavior is assigned downstream.
- Each vertical has an explicit core-version and upstream-update policy.
- Customer repositories use pinned vertical releases and exclude production secrets and records.
- Runtime extraction work is listed in the runtime implementation ledger rather than claimed complete by this documentation slice.

## Tests

- Review repo ownership against existing business-ops and auto-repair artifacts.
- Verify links and repository names against the plan and roadmap.
- Run repo verification and manifest integrity checks.
