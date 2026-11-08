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
| RI-00 | Inventory current runtime behavior and identify implemented, partial, missing, and conflicting surfaces before estimating work | `lumina-biz` | Slices 73-81 review | Completed |
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

RI-00 is an audit, not a rewrite. The source-level baseline below records what exists in the `lumina-biz` checkout as of 2026-11-08; re-check the relevant tests before implementation estimates are committed.

## Baseline Audit Snapshot

| Area | Existing runtime | Remaining gap |
|---|---|---|
| Gear 1 / deterministic UI | `src/web/app.tsx`, `src/web/src/services/uiMode.ts`, slash-command services, plugin registration, and UI tests provide mode switching and deterministic command dispatch. | Gear 1 is still chat-centric; a task-focused POS/operator workspace and its screen registry/context contract are not present as a complete runtime surface. |
| Gear 2 / assistant | The existing chat path calls the assistant flow, and decision-precedent confirmation is implemented. | No assistant side drawer, screen-scoped context lock, staged form-draft workflow, or context-lock telemetry contract was found in the frontend runtime. |
| Business connectors | ERPNext and Odoo connector modules, fixture adapters, and a provider conformance harness exist under `src/lumina/business_ops/connectors/`. | This is not yet a complete generic POS, labor, payroll, and accounting capability runtime across providers. |
| Document ingestion | `src/lumina/ingestion/extractors.py` extracts generic PDF, DOCX, Markdown, CSV, JSON, and YAML text; `interpreter.py` provides generic SLM interpretation. | No invoice-specific VLM/OCR, line-item validation, price-anomaly workflow, or restaurant receiving handoff was found in first-party runtime code. |
| Recipe and units | No first-party UoM conversion, yield calculation, or recipe-to-BOM implementation was found in `src/lumina` or `model-packs/business-ops`. | The deterministic conversion, provenance, review, and draft-write path remain to be implemented in the restaurant vertical. |
| Compute cascade | spaCy/regex processing, glossary and vector routing, SLM calls, an LLM path, and degraded-reason tracking exist across `src/lumina/core/` and `src/lumina/api/processing.py`. | The components need an integrated, tested four-stage cascade with explicit transition, evidence, and degraded-mode acceptance; avoid replacing existing stages wholesale. |
| Edge deployment | A single-box health-check script, local-first SLM defaults, and single-box deployment documentation exist. | No complete edge-node lifecycle, offline recovery, versioned upgrade, or rollback runtime was found. |
| Repository separation | The `business-ops` pack contains an `auto-repair` module. | No separate `lumina-restaurants`, `lumina-autorepair`, or `lumina-cstore` checkout is present in this workspace; restaurant and c-store modules and customer solution repos are not yet established here. |

This snapshot is an inventory, not proof that each existing surface meets its contract. RI-02 through RI-09 must add behavior-level tests around the existing partial implementations rather than duplicate them.

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
