---
title: "Slice 76 - Generic POS and Back-Office Capability Contract"
slice: 76
status: planned
version: 1.0.0
last_updated: 2026-11-17
---

## Purpose

Define the provider-neutral capability boundary between `lumina-biz`, public verticals, and POS/back-office systems of record. Reuse the canonical connector envelopes and taxonomy rather than creating a second provider API.

## Scope

- Define POS, labor, payroll, accounting, and back-office capability families.
- Define capability declaration, discovery, provider mapping, and conformance boundaries.
- Define query, draft, commit-request, cancellation-request, and event-sync semantics.
- Define deterministic, no-model analytics over authorized systems-of-record data.
- Preserve external systems of record as authoritative for their data domains.
- Define API-only cross-domain access, unsupported-operation responses, and safe fallback semantics.

## Out of Scope

- Production connector transports or provider parity implementation.
- Restaurant menu, recipe, or receiving rules.
- Vendor-specific POS/ERP behavior or F&B-only formulas in `lumina-biz`.
- Replacing customer systems of record.
- Using LLM, SLM, VLM, or audio-model calls for routine known calculations or reports.

## Required Changes

- Reference the canonical capability namespaces and action classes in `docs/7-concepts/business-system-capability-taxonomy.md`.
- Specify how requests and results conform to `business-operation-request-schema-v1.json` and `business-operation-result-schema-v1.json`.
- Specify that connector manifests declare supported namespace/action pairs using `business-system-connector-manifest-schema-v1.json`.
- Preserve those per-namespace action pairs in connector registry entries. New registry producers must provide the exact `capabilities` declaration; when both exact declarations and legacy flattened summaries are present, their namespace sets and action unions must agree. Legacy flattened summaries without exact declarations are accepted only when unambiguous (a single namespace or a single action); ambiguous multi-namespace/multi-action entries must provide exact declarations.
- Define provider mapping, capability discovery, conformance, structured unsupported-operation errors, and fallback rules.
- Define Tool Token scope, organization/site/actor binding, runtime-secret references, idempotency, and auditable human approval for mutations.
- Define deterministic analytics provenance and the boundary that reserves AI for unresolved ambiguity or requested qualitative synthesis.

## New/Changed Contracts

- `pos_back_office_capability_contract_v1`
- `provider_connector_capability_map_v1`
- `sor_authority_boundary_contract_v1`
- `deterministic_analytics_result_provenance_v1`

## Capability and Operation Semantics

Capabilities are requested by canonical namespace and action class, not by provider name or provider-specific document/table names. Relevant capability families include POS sales, item/catalog, inventory, purchasing/receiving, service/work orders, scheduling/timekeeping, accounting/invoices, and back-office reports. The taxonomy remains the namespace authority; adding a namespace or action requires a separately reviewed taxonomy/schema change.

Use the existing canonical request/result schemas. Requests identify a request, action, namespace, actor scope, request time, and safe payload. Results correlate to the request and identify status, occurrence time, optional target reference, result data, and normalized errors. Connector and routing metadata such as connector choice, correlation, idempotency, and policy version belongs in the existing routing/execution records and must not silently alter provider-neutral payloads.

Action semantics:

- `query` reads or aggregates data from the authoritative system. It does not create, update, or commit business records.
- `create_draft` and `update_draft` stage reviewable changes and return a target reference and draft state. They do not represent a committed system-of-record mutation.
- `request_commit` and `request_cancel` express an intent for the authoritative provider to perform the operation. They require current actor/tool authorization, policy and idempotency checks, and any required human approval; they do not bypass the Slice 41 live-execution gate.
- `sync_event` reports a provider event through the declared connector boundary and preserves source identity and deduplication information.

## Deterministic Analytics Boundary

Routine reporting and calculations over authorized ledger data run as deterministic CPU work without LLM, SLM, VLM, or audio-model calls and without token generation. Examples include trends, seasonal velocity curves, rolling averages, exponential smoothing, daypart histograms, par levels, FIFO or moving-average inventory valuation, and basic reorder triggers.

Each result must identify the calculation or policy version, source/system-of-record, input time window and site time zone, units and precision, source freshness/time, and missing-data behavior so an operator can reproduce it. The system of record remains authoritative for stored transactions and configured inventory valuation; local calculations may summarize authorized data but may not silently post adjustments. Invoke AI only when deterministic results leave material ambiguity, evidence conflicts or is incomplete, an anomaly requires interpretation, or the operator requests qualitative synthesis. Any resulting explanation or suggestion remains separate from deterministic values and cannot authorize a mutation.

Verticals may configure formulas, thresholds, units, and schedules. F&B recipe/yield and daypart-specific rules belong downstream in `lumina-fnb`; `lumina-biz` owns only reusable calculation and provenance mechanics.

## Unsupported Operations and Fallback

- A connector manifest must declare support for the requested namespace/action pair before routing.
- An undeclared namespace or action returns a structured, non-retryable unsupported-capability/action error; it must not be guessed, silently remapped, or sent to an arbitrary provider.
- Fallback may select only an explicitly configured, healthy connector that declares the same capability and is authorized for the same organization/site scope.
- Read-only queries may be retried or failed over under the configured policy and must preserve request/correlation identity.
- Draft or mutation operations must not be automatically replayed to another provider when the first outcome is unknown. Require idempotency and resolve the first provider's outcome before retry or failover.
- If no eligible provider is available, return an explicit unavailable/degraded result. Never fabricate live data or use an LLM to stand in for a failed system-of-record query.

## Acceptance Criteria

- Capabilities are vendor-neutral and reusable by distinct verticals.
- Provider-specific behavior is isolated behind connector mappings.
- Requests/results validate against the canonical schemas, and provider support is checked against manifest declarations.
- Routing honors the declared action set for the requested namespace; it never infers a cross-product when exact declarations are present.
- External systems of record retain authority over their domains.
- Cross-domain operations use target-domain APIs and are auditable; Tool Token and actor scope are enforced at dispatch.
- Routine analytics are reproducible, CPU-first calculations with provenance and make zero model calls.
- Ambiguity escalation is explicit and cannot replace deterministic values or authorize a system-of-record mutation.
- Unsupported capabilities and unavailable providers fail explicitly; mutation fallback cannot duplicate uncertain writes.

## Tests

- Review example capability payloads against existing connector contracts.
- Validate request/result and connector-manifest examples against the canonical schemas.
- Verify Tool Token scope, unsupported-operation errors, same-capability fallback, and uncertain mutation outcomes.
- Verify deterministic analytics provenance, zero model calls on routine calculations, and explicit ambiguity escalation.
- Run repo verification and manifest integrity checks.
