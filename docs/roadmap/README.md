---
title: "Lumina Biz Roadmap"
version: 1.9.0
last_updated: 2026-11-08
---

# Lumina Biz Roadmap

**Version:** 1.9.0
**Status:** Active
**Last updated:** 2026-11-08

---

## Overview

The `lumina-biz` roadmap tracks the shared business core built on `lumina-framework`, followed by distinct vertical repositories and downstream private customer solutions. Each slice has explicit scope, dependencies, and acceptance criteria.

Each slice is documented under `docs/roadmap/slices/`. Closely related documentation slices may be delivered in a small dependency-oriented PR bundle; runtime implementation remains separately tracked and must target its owning repository.

---

## Slice Index

| Slice | Title | Status |
|-------|-------|--------|
| [01](slices/01-framework-boundary.md) | Framework Boundary and Final Shape Documentation | Active |
| [02](slices/02-system-update-vocabulary.md) | System Update Vocabulary | Active |
| [03](slices/03-request-intake-and-classification.md) | Request Intake and Classification | Active |
| [04](slices/04-system-pack-authority-gate.md) | System Pack Authority Gate | Active |
| [05](slices/05-system-pack-sole-coding-agent-ingress.md) | System Pack as Sole Coding Agent Ingress | Active |
| [06](slices/06-coding-agent-model-pack-architecture-v2.md) | Coding Agent Model Pack Architecture V2 | Active |
| [07](slices/07-coding-agent-pack-skeleton.md) | Coding Agent Pack Skeleton | Delivered |
| [08](slices/08-job-intake-micro-context.md) | Job Intake and Micro-Context Injector | Delivered |
| [09](slices/09-context-staging-and-job-interpretation.md) | Context Staging and Job Interpretation | Delivered |
| [10](slices/10-tool-call-policy-enforcement.md) | Tool-Call Policy Enforcement & Real Test Runner | Delivered |
| [11](slices/11-three-tier-execution-interface.md) | Three-tier Execution Interface | Delivered |
| [12](slices/12-tier-2-decomposer.md) | Tier-2 Decomposer & DAG Planner | Delivered |
| [13](slices/13-tier-1-architect.md) | Tier-1 Architect & SLM Routing | Delivered |
| [14](slices/14-dag-correct-compute-orchestration.md) | DAG-Correct Compute Orchestration | Delivered |
| [15](slices/15-tier3-execution-gating.md) | Tier-3 Execution Gating and Retry Policy | Delivered |
| [16](slices/16-execution-state-persistence.md) | Execution State Persistence & Checkpoint Recovery | Delivered |
| [17](slices/17-multi-slice-orchestration-loop.md) | Multi-Slice Orchestration Loop | Delivered |
| [18](slices/18-orchestration-hardening-and-determinism.md) | Orchestration Hardening and Determinism | Delivered |
| [19](slices/19-execution-telemetry-and-trace-export.md) | Execution Telemetry and Trace Export | Delivered |
| [20](slices/20-tiered-model-and-api-key-routing.md) | Tiered Model and API Key Routing | Delivered |
| [21](slices/21-framework-boundary-reconciliation.md) | Framework Boundary Reconciliation | Delivered |
| [22](slices/22-system-pack-activation-gate.md) | System Pack Approval / Activation Gate | Delivered |
| [23](slices/23-evidence-harvest-and-teardown.md) | Evidence Harvest and Teardown | Delivered |
| [24](slices/24-system-led-evidence-commit-and-teardown-confirmation.md) | System-Led Evidence Commit and Teardown Confirmation | Delivered |
| [25](slices/25-b2b-workstream-boundary-and-task-graph.md) | B2B Workstream Boundary and Global Task Graph | Planned |
| [26](slices/26-tenant-site-actor-memory-contracts.md) | Tenant/Site/Actor Memory Contracts | Delivered |
| [27](slices/27-institutional-vector-memory-layer.md) | Institutional Vector Memory Layer | Delivered |
| [28](slices/28-semantic-thread-routing-and-forking.md) | Semantic Thread Routing and Context Forking | Delivered |
| [29](slices/29-decision-precedent-confidence-and-escalation.md) | Decision Precedent, Confidence, and Escalation | Planned |
| [30](slices/30-erpnext-adapter-foundation-and-fixtures.md) | Canonical Business-System Contracts and Capability Taxonomy | Delivered |
| [31](slices/31-business-ops-pack-bootstrap.md) | Connector Registry and Capability Routing | Delivered |
| [32](slices/32-auto-repair-mvp-and-single-box-deployment.md) | Business Ops Pack Bootstrap | Delivered |
| [33](slices/33-erpnext-reference-connector-and-fixtures.md) | ERPNext Reference Connector and Deterministic Fixtures | Delivered |
| [34](slices/34-secondary-provider-connector-and-conformance-harness.md) | Secondary Provider Connector and Conformance Harness | Delivered |
| [35](slices/35-auto-repair-mvp-over-connector-abstractions.md) | Auto Repair MVP Over Connector Abstractions | Delivered |
| [36](slices/36-single-box-deployment-and-operational-hardening.md) | Single-Box Deployment and Operational Hardening | Planned |
| [37](slices/37-erp-identity-authority-and-claim-contract.md) | ERP Identity Authority and Claim Contract | Active |
| [38](slices/38-erp-jwt-verification-gateway-and-auth-transition.md) | ERP JWT Verification Gateway and Auth Transition | Delivered |
| [39](slices/39-generic-erp-service-core-and-vertical-profile-layer.md) | Generic ERP Service Core and Vertical Profile Layer | Planned |
| [40](slices/40-architecture-coherence-enforcement-hardening.md) | Architecture Coherence Enforcement Hardening | Planned |
| [41](slices/41-erp-integration-program-charter-and-dependency-lock.md) | ERP Integration Program Charter and Dependency Lock | Active |
| [42](slices/42-erp-trust-runtime-and-live-actor-liveness-adapter.md) | ERP Trust Runtime and Live Actor-Liveness Adapter | Planned |
| [43](slices/43-generic-connector-transport-runtime.md) | Generic Connector Transport Runtime | Planned |
| [44](slices/44-mutation-safety-and-idempotency-ledger.md) | Mutation Safety and Idempotency Ledger | Planned |
| [45](slices/45-erpnext-live-execution-adapter-and-error-normalization.md) | ERPNext Live Execution Adapter and Error Normalization | Planned |
| [46](slices/46-connector-operational-resilience-and-tenant-fairness.md) | Connector Operational Resilience and Tenant Fairness | Planned |
| [47](slices/47-credential-lifecycle-and-secret-rotation-integration.md) | Credential Lifecycle and Secret Rotation Integration | Planned |
| [48](slices/48-production-cutover-gates-and-rollback-automation.md) | Production Cutover Gates and Rollback Automation | Planned |
| [49](slices/49-secondary-provider-adapter-parity.md) | Secondary Provider Adapter Parity | Planned |
| [50](slices/50-post-parity-hardening-slo-enforcement-and-governance-closeout.md) | Post-Parity Hardening, SLO Enforcement, and Governance Closeout | Planned |
| [51](slices/51-framework-boundary-lock-and-pack-taxonomy-reconciliation.md) | Framework Boundary Lock and Pack Taxonomy Reconciliation | Delivered |
| [52](slices/52-domain-pack-authoring-contract-v1.md) | Domain Pack Authoring Contract v1 | Delivered |
| [53](slices/53-module-authoring-contract-v1.md) | Module Authoring Contract v1 | Delivered |
| [54](slices/54-module-glossary-and-index-contract.md) | Module Glossary and Index Contract | Planned |
| [55](slices/55-knowledge-index-rebuild-and-drift-elimination.md) | Knowledge Index Rebuild and Drift Elimination | Planned |
| [56](slices/56-turn-interpreter-contract-v1.md) | Turn Interpreter Contract v1 | Planned |
| [57](slices/57-deterministic-pre-llm-domain-to-module-routing.md) | Deterministic Pre-LLM Domain-to-Module Routing | Planned |
| [58](slices/58-module-command-surface-contract-v1.md) | Module Command Surface Contract v1 | Planned |
| [59](slices/59-workflow-definition-contract-and-dag-compilation.md) | Workflow Definition Contract and DAG Compilation | Planned |
| [60](slices/60-workflow-state-durability-and-recovery.md) | Workflow State Durability and Recovery | Planned |
| [61](slices/61-generic-connector-contract-consolidation.md) | Generic Connector Contract Consolidation | Planned |
| [62](slices/62-erp-auth-cutover-wiring.md) | ERP Auth Cutover Wiring | Planned |
| [63](slices/63-neutral-reference-vertical-exemplar-pack.md) | Neutral Reference Vertical Exemplar Pack | Planned |
| [64](slices/64-multi-site-and-cross-location-aggregation-contract.md) | Multi-Site and Cross-Location Aggregation Contract | Planned |
| [65](slices/65-pack-extraction-tooling-and-vertical-repository-template.md) | Pack Extraction Tooling and Vertical Repository Template | Planned |
| [66](slices/66-authoring-guides-and-extraction-readiness-closeout.md) | Authoring Guides and Extraction Readiness Closeout | Planned |
| [67](slices/67-site-profile-and-capability-declaration-contract-v1.md) | Site Profile and Capability Declaration Contract v1 | Planned |
| [68](slices/68-capability-gated-workflow-and-task-eligibility-contract-v1.md) | Capability-Gated Workflow and Task Eligibility Contract v1 | Planned |
| [69](slices/69-role-catalog-assignment-and-notification-routing-contract-v1.md) | Role Catalog, Assignment, and Notification Routing Contract v1 | Planned |
| [70](slices/70-site-variance-and-role-aware-reference-scenarios.md) | Site-Variance and Role-Aware Reference Scenarios | Planned |
| [71](slices/71-operational-overrides-profile-versioning-and-change-governance.md) | Operational Overrides, Profile Versioning, and Change Governance | Planned |
| [72](slices/72-vertical-extraction-and-configuration-portability-gate.md) | Vertical Extraction and Configuration Portability Gate | Planned |
| [73](slices/73-vertical-decontamination-and-generic-base-lock.md) | Business Core and Vertical Repository Boundary | Active |
| [74](slices/74-dual-mode-ui-shell-and-gear-1-deterministic-surface.md) | Dual-Mode UI Shell and Gear 1 Deterministic Surface | Planned |
| [75](slices/75-gear-2-assistant-drawer-and-context-locking-telemetry.md) | Gear 2 Assistant Drawer and Context-Locking Telemetry | Planned |
| [76](slices/76-generic-pos-back-office-capability-contract.md) | Generic POS and Back-Office Capability Contract | Planned |
| [77](slices/77-restaurant-vertical-repo-charter-and-pack-boundary.md) | F&B Vertical Repo Charter and Pack Boundary | Planned |
| [78](slices/78-invoice-vlm-ingestion-contract.md) | Invoice VLM Ingestion Contract | Planned |
| [79](slices/79-unit-of-measure-and-recipe-yield-contract.md) | Unit-of-Measure and Recipe/Yield Contract | Planned |
| [80](slices/80-neurosymbolic-compute-cascade-contract.md) | Neurosymbolic Compute Cascade Contract | Planned |
| [81](slices/81-edge-deployment-node-integration.md) | Edge Deployment Node Integration | Planned |

## Current Direction

Numbered slice files are retained as planning records, but autogenerated numbering does not define product names, vertical priority, or implementation completion. The authoritative SMB capability scope is [SMB Operations Product Direction](smb-operations-product-direction.md); runtime work is separately tracked in [runtime-implementation-program.md](runtime-implementation-program.md). Slice 53 was merged in PR #55.

The business repository layers and their release/update path are defined in [business-repository-topology.md](../7-concepts/business-repository-topology.md). Related documentation may be grouped into a few capability-oriented PRs. Runtime implementation proceeds by direct prerequisite, not by waiting for unrelated vertical documentation to finish.

---

## Alignment Note

Slice 1 preserved the initial follow-up roadmap as the planning record at that
time. This index is the active discoverability surface for the implementation
sequence that actually followed. When the two differ, use this index for current
slice ordering and use Slice 1 for the authoritative framework-boundary
invariants it established.

## Direction Lock

Slice 39 hard-locks the ERP integration direction to a reusable generic service core with profile-layer variance. Until explicitly superseded, new vertical onboarding work should extend profile and mapping layers first rather than introducing core workflow forks.

## Operational Note (Temporary CI Fallback)

While GitHub-hosted CI is unstable, Slice 39 delivery uses a local full-workflow
pre-merge gate that mirrors the `CI Tests` workflow intent.

Required baseline before merge:

- `./scripts/run-full-verification.ps1`
- backend coverage gate: `pytest ... --cov-fail-under=85`
- frontend unit/coverage/e2e sequence from workflow

This temporary fallback remains active until 5 consecutive green `CI Tests`
workflow runs are observed on `main`. Sunset and re-enable procedures are
defined in Slice 39.

## Dependency Graph (Architecture Coherence)

Lumina tracks two graph categories:

- Runtime execution DAG lineage (Slices 12 and 14).
- Delivery dependency DAG for post-Slice 38 enforcement closure.

Architecture coherence DAG nodes:

- N1 Tool-token boundary enforcement.
- N2 Institutional-memory ingest guardrails.
- N3 Pipeline order enforcement (actor auth -> NLP -> semantic routing -> PPA).
- N4 Cross-domain API-only execution boundary.
- N5 Daemon audit-commit parity.
- N6 Active SoR actor-liveness verification.

Dependency edges:

- N1 -> N4
- N1 -> N5
- N1 -> N6
- N2 -> N6
- N3 -> N5

Unblock criteria:

- N1 complete when unauthorized tool calls are structurally excluded and tested.
- N2 complete when chat/conversation payload classes are rejected at ingest.
- N3 complete when strict ordering checks are enforced or explicit degraded-mode telemetry is emitted.
- N4 complete when cross-domain direct state access is blocked outside API paths.
- N5 complete when daemon operations require the same audit commitment guarantees as API paths.
- N6 complete when SoR liveness check policy is implemented with deterministic fallback behavior.

## Slice 41 Execution Gate

Slice 41 is active and governs post-Slice-40 ERP execution sequencing. Runtime
implementation for Slices 42-50 is hard-gated until Slice 40 nodes N1, N2, and
N3 are closed with explicit closure evidence.

Allowed while gate is closed:

- Documentation refinements and dependency clarifications.
- Test-design planning and evidence-template preparation.

Blocked while gate is closed:

- Runtime implementation for ERP trust adapters, transport execution, live
  mutation paths, provider parity execution, and cutover automation.

## Prior Framework Planning Backlog (Slices 51-72)

This program records the earlier framework-finalization plan and its dependency
graph. Slices 54-72 remain preserved for traceability, but are not the current
execution order until explicitly reconciled with the business-core and vertical
repository topology.

Program phases:

- **Phase A — Framework hardening contracts:** Slices 51-62.
- **Phase B — Reference vertical proof:** Slices 63-64.
- **Phase C — Extraction readiness:** Slices 65-66.
- **Phase D — Declarative site variance and portability proof:** Slices 67-72.

Program backbone:

- [Phase A hardening contracts: 51-62]
           |
- [Phase B reference vertical: 63-64]
           |
- [Phase C extraction readiness: 65-66]
           |
- [Phase D site variance and portability: 67-72]

Critical invariant:

- Site variance, role assignment, workflow/task eligibility, and notification
  routing must be declarative configuration. They must never require
  per-location runtime forks, site-specific conditional code paths, or
  hardcoded recipient logic.

Dependency chain:

- 51 -> 52 -> 53 -> 54 -> 55 -> 56 -> 57 -> 58 -> 59 -> 60
- 52 -> 61
- 38 -> 62
- 59 -> 62
- 60 -> 63
- 61 -> 63
- 62 -> 63
- 63 -> 64 -> 65 -> 66
- 52 -> 67
- 53 -> 67
- 59 -> 68
- 67 -> 68
- 67 -> 69
- 63 -> 70
- 64 -> 70
- 68 -> 70
- 69 -> 70
- 67 -> 71
- 68 -> 71
- 69 -> 71
- 70 -> 72
- 71 -> 72
- 65 -> 72
- 66 -> 72

Slice 41 relation:

- Slices 51-72 are planning/documentation-only and may proceed while the Slice
  41 hard gate for runtime implementation in Slices 42-50 remains active.
- The Slice 41 hard gate applies specifically to ERP runtime implementation
  paths defined in Slices 42-50; it does not globally block unrelated
  non-ERP framework hardening implementation.
- Any runtime implementation generated from Slices 51-72 that intersects ERP
  execution paths must still respect Slice 41 gating and dependency locks.
- Slice 41 already locks Lumina to reusable profile-layer variance over a shared
  core. Slices 67-72 extend that principle to site profiles, role catalogs, and
  notification routing so location differences stay in configuration and do not
  reopen framework-fork pressure.

---

## Roadmap Posture

`lumina-framework` is the generic engine. Its framework boundary and three base
model packs remain governed by
[`framework-boundary.md`](../7-concepts/framework-boundary.md).

`lumina-biz` is the shared business core built on that engine. Generic business
capabilities remain here; F&B, convenience/fuel, dry retail, and auto care,
repair, and towing behavior belongs in the public `lumina-fnb`, `lumina-cstore`,
`lumina-retail`, and `lumina-auto` repositories. Private customer solutions
consume a tagged vertical release and hold only customer-scoped configuration
or approved extensions.

The ownership and release policy is defined in
[`business-repository-topology.md`](../7-concepts/business-repository-topology.md).
Runtime implementation is tracked separately in
[`runtime-implementation-program.md`](runtime-implementation-program.md).
Its Active Runtime Dependency DAG is the current implementation order; the
51-72 dependency graph above is retained only as historical planning context.

---

## Convention

Each slice document uses the following structure:

```markdown
## Purpose
## Scope
## Out of Scope
## Required Changes
## New/Changed Contracts
## Files Likely Touched
## Acceptance Criteria
## Tests
## Ledger/Governance Impact
## Follow-Up Slices
```
