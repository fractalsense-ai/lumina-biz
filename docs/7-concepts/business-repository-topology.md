---
title: "Business Repository Topology"
version: 1.0.0
status: active
last_updated: 2026-11-08
---

# Business Repository Topology

## Purpose

Define the repository and release boundaries from the generic Lumina engine through shared business capabilities, industry verticals, and customer-specific solutions.

## Repository Layers

| Layer | Repository | Owns | Must not own |
|---|---|---|---|
| Generic engine | `lumina-framework` | Model-pack runtime, orchestration primitives, identity and governance foundations | Business vertical policy or customer-specific behavior |
| Business core | `lumina-biz` | Reusable business workflows and capability contracts, provider-neutral connector surfaces, shared business UI and operational primitives | Restaurant-, auto-repair-, or convenience-store-only rules |
| Vertical product | `lumina-restaurants`, `lumina-autorepair`, `lumina-cstore` | Industry workflows, domain modules, vertical schemas, provider mappings, fixtures, and product acceptance tests | Copies of generic engine/core behavior that should be upstreamed |
| Customer solution | Private customer repository, derived from a vertical release | Customer-approved configuration, deployment overlays, and narrowly scoped extensions | Secrets, production records, or an independently forked copy of the full platform |

`lumina-biz` is the reusable core for Lumina's business product line. It is not a replacement for the lower-level `lumina-framework`, and it is not a single repository that accumulates every industry implementation.

## Fork and Upstream Policy

Each vertical repository is a distinct fork from a tagged `lumina-biz` baseline, giving it independent release control while retaining upstream lineage. Each vertical must record the base tag/commit, keep an explicit upstream update path, and run compatibility tests before syncing newer core changes.

A fork is not permission for indefinite divergence. Generic fixes and capabilities belong in `lumina-biz`; industry-specific behavior belongs in the corresponding vertical. Promote a change upstream when it is reusable across at least two verticals or is an agreed core capability.

Private customer solution repositories are created from a tagged vertical release. They should contain only customer configuration, deployment definitions, and approved extensions. Create customer-specific runtime forks only when a documented requirement cannot be satisfied through supported configuration or extension points.

## Change Flow

1. Generic engine behavior is implemented in `lumina-framework` and released independently.
2. Shared business behavior is implemented in `lumina-biz` against a compatible engine version.
3. Each vertical records its `lumina-biz` base tag/commit and validates its changes against the core conformance suite.
4. A customer solution is forked from a tagged vertical release and adds only customer-scoped configuration or extensions.
5. Upstream changes flow from engine to business core, then through vertical compatibility PRs, then into customer solution updates.

## Data and Secret Boundaries

Source repositories may contain schemas, synthetic fixtures, non-secret defaults, and deployment templates. They must not contain customer production data, credentials, access tokens, or raw operational chat transcripts. Customer secrets belong in the deployment's secret-management system; business records remain in their designated systems of record.

## Release and Compatibility Gates

- `lumina-biz` publishes versioned releases with a declared compatible `lumina-framework` range.
- Each vertical records the upstream `lumina-biz` base and passes core contract/conformance tests before release.
- Customer solutions record their vertical base tag and pass deployment, migration, and end-to-end acceptance checks before upgrade.
- Breaking changes require an explicit migration note and a staged upgrade path at every downstream layer.

## Decision Rule

When deciding repository ownership, ask whether the behavior is shared across business verticals, industry-specific, or customer-specific. Place it in `lumina-biz`, a named vertical repo, or the private customer solution respectively. Do not solve a lower-layer limitation with a higher-layer fork when a reusable lower-layer change is appropriate.
