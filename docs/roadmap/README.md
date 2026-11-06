version: 1.4.0
last_updated: 2026-09-22
---

# Lumina Framework Roadmap

**Version:** 1.4.0
**Status:** Active
**Last updated:** 2026-09-22

---

## Overview

The Lumina Framework roadmap is delivered one slice at a time. Each slice is
a focused, reviewable unit of work with explicit scope, contracts, and
acceptance criteria.

Slices are numbered sequentially. Each slice is documented in its own file
under `docs/roadmap/slices/` and delivered as a focused PR.

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
| [51](slices/51-framework-boundary-lock-and-pack-taxonomy-reconciliation.md) | Framework Boundary Lock and Pack Taxonomy Reconciliation | Planned |
| [52](slices/52-domain-pack-authoring-contract-v1.md) | Domain Pack Authoring Contract v1 | Planned |
| [53](slices/53-module-authoring-contract-v1.md) | Module Authoring Contract v1 | Planned |
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

## Framework Finalization Program DAG (Slices 51-66)

Program objective: finalize Lumina as a reusable framework first, then prove
the authoring/execution shape with a neutral reference vertical, then define
repeatable extraction into business-specific repositories.

Program phases:

- **Phase A — Framework hardening contracts:** Slices 51-62.
- **Phase B — Reference vertical proof:** Slices 63-64.
- **Phase C — Extraction readiness:** Slices 65-66.

Dependency chain:

- 51 -> 52 -> 53 -> 54 -> 55 -> 56 -> 57 -> 58 -> 59 -> 60
- 52 -> 61
- 38 -> 62
- 59 -> 62
- 60 -> 63
- 61 -> 63
- 62 -> 63
- 63 -> 64 -> 65 -> 66

Slice 41 relation:

- Slices 51-66 are planning/documentation-only and may proceed while the Slice
  41 hard gate for runtime implementation in Slices 42-50 remains active.
- The Slice 41 hard gate applies specifically to ERP runtime implementation
  paths defined in Slices 42-50; it does not globally block unrelated
  non-ERP framework hardening implementation.
- Any runtime implementation generated from Slices 51-66 that intersects ERP
  execution paths must still respect Slice 41 gating and dependency locks.

---

## Roadmap Posture

The repository is being finalised into the reusable base framework. The final
base framework consists of exactly three model packs:

- **System Model Pack** — sole governance/authority/ingress layer
- **Coding Agent Model Pack** — bounded artifact factory
- **Template Model Pack** — reusable approved framework template shapes

Domain packs currently in the repository (`business-ops`) are provisional
scaffolding used while validating the framework shape. They
will be extracted, moved, or removed in later PRs.

See [`docs/7-concepts/framework-boundary.md`](../7-concepts/framework-boundary.md)
for the authoritative framework boundary contract.

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
