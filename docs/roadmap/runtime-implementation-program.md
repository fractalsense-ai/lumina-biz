---
title: "Runtime Implementation Program"
version: 1.0.0
status: active
last_updated: 2026-11-08
---

# Runtime Implementation Program

## Purpose

Track the code and integration work that follows the contract-first slices. The 73-81 slice series defines boundaries and contracts; it does not, by itself, deliver the working product. Runtime work is assigned to the repository that owns the behavior.

## Delivery Rule

Implement a runtime workstream after its directly required contract bundle is accepted. Do not wait for unrelated vertical contracts to finish, and do not start a runtime change without a linked slice/PR scope, executable acceptance criteria, tests, and an owning repository.

## Workstream Ledger

| ID | Runtime outcome | Owning repository | Contract prerequisites | Status |
|---|---|---|---|---|
| RI-00 | Inventory current runtime behavior and identify implemented, partial, missing, and conflicting surfaces before estimating work | `lumina-biz` | Slices 73-81 review | Active |
| RI-01 | Establish the business-core package/release boundary and remove or relocate only vertical-specific behavior; preserve shared business capabilities | `lumina-biz` | 73, 76 | Planned |
| RI-02 | Deliver Gear 1 deterministic operator screens, permission-aware commands, and screen-context handling | `lumina-biz` | 74, RI-01 | Planned |
| RI-03 | Deliver Gear 2 assistant drawer, screen context lock, staged drafts, human approval, and privacy-safe telemetry | `lumina-biz` | 75, RI-02 | Planned |
| RI-04 | Implement provider-neutral POS and back-office capability interfaces, adapters, and conformance tests | `lumina-biz` | 76, RI-01 | Planned |
| RI-05 | Bootstrap `lumina-restaurants` from a tagged business-core release with independent CI and core compatibility tests | `lumina-restaurants` | 77, RI-01 | Planned |
| RI-06 | Implement local-first invoice intake, extraction review, anomaly flags, and staged receiving handoff | `lumina-restaurants` | 78, RI-05 | Planned |
| RI-07 | Implement deterministic unit conversion and reviewed recipe/yield-to-BOM drafts | `lumina-restaurants` | 79, RI-05, RI-06 | Planned |
| RI-08 | Implement the four-stage compute cascade with deterministic ordering, bounded model calls, and degraded-mode evidence | `lumina-biz` plus vertical configuration | 80, RI-01, RI-03 | Planned |
| RI-09 | Deliver local-first edge packaging, offline/degraded operation, and upgrade/rollback behavior | `lumina-biz` plus vertical deployment | 81, RI-08 | Planned |
| RI-10 | Bootstrap `lumina-autorepair` from a tagged business-core release and port only auto-repair-owned modules and tests | `lumina-autorepair` | 73, 76, RI-01 | Planned |
| RI-11 | Bootstrap `lumina-cstore` from a tagged business-core release and port only convenience-store-owned modules and tests | `lumina-cstore` | 73, 76, RI-01 | Planned |
| RI-12 | Establish private customer solution repos from supported vertical releases, with configuration, deployment, upgrade, and acceptance gates | Customer private repo(s) | Vertical release; topology contract | Planned |

RI-00 is an audit, not a rewrite. It must map existing code and tests to the outcomes above so work already present is credited and duplicate implementation is avoided.

## Dependency Order

- RI-00 precedes scope commitment for every implementation workstream.
- RI-01 precedes shared UI and vertical bootstrap work.
- RI-02 precedes RI-03 because the assistant is a context-scoped sidecar to the deterministic operator surface.
- RI-04 and RI-05 may proceed after RI-01; RI-05 must pin a released core baseline.
- RI-06 and RI-07 are restaurant-owned and depend on RI-05; their contracts must preserve human review before operational mutation.
- RI-08 may proceed once its contract is accepted and required core/vertical inputs are available; it must not become an unbounded model router.
- RI-09 follows a verified local runtime and cascade; it includes failure and recovery tests.
- RI-10 and RI-11 reuse the released business core independently; they must not block restaurant delivery.
- RI-12 begins only after a vertical has a supportable release and a customer-specific configuration boundary.

## Per-Workstream Gates

Every runtime PR must:

- target the owning repository shown above;
- link the relevant contract slice and state explicit out-of-scope behavior;
- include unit and integration tests for the changed behavior, plus vertical conformance tests where applicable;
- pass repository verification and manifest integrity checks;
- preserve systems-of-record authority and human approval for mutations;
- respect Slice 41's hard gate for any ERP execution, live transport, or mutation path until its closure criteria are satisfied;
- keep customer data and secrets out of source control; and
- document release compatibility and downstream upgrade impact.

## Contract Documentation Groups

To avoid one PR per documentation slice while preserving review boundaries, group the 73-81 contracts by dependency:

1. Slices 73-76: business-core boundary, deterministic UI, assistant boundary, and shared capability contracts.
2. Slices 77-79: vertical repository charter, invoice intake, and unit/recipe contracts.
3. Slices 80-81: compute cascade and edge deployment contracts.

These groups may be reviewed in one roadmap-alignment PR or a few PRs, provided each included slice and its acceptance evidence are listed. Runtime implementation is released separately in code PRs using RI-00 through RI-12; documentation-bundle merge does not count as runtime delivery.
