---
title: "SMB Operations Product Direction"
version: 1.0.0
status: active
last_updated: 2026-11-08
---

# SMB Operations Product Direction

## Purpose

Capture the intended SMB product family and capability boundaries for `lumina-biz`. This is a product-direction brief, not an implementation commitment or a generated slice sequence. Runtime work remains in the workstream ledger and must be sized against the code that exists.

## Product and Repository Model

- `lumina-framework` is the generic orchestration and governance engine.
- `lumina-biz` is the shared business core for small and medium-sized businesses. It owns reusable operator UI primitives, identity and authorization integration, task and connector contracts, audit controls, and shared runtime capabilities.
- Public vertical repositories fork a tagged `lumina-biz` baseline and own their industry workflows, domain rules, integrations, fixtures, and product acceptance tests.
- Private customer repositories are created only for customer-specific deployments and approved extensions, based on a tagged public vertical release.

| Public vertical | Intended scope |
|---|---|
| `lumina-fnb` | Food and beverage operations, including restaurant and food-service workflows |
| `lumina-cstore` | Convenience-store and fuel operations |
| `lumina-retail` | Standard dry-goods retail operations |
| `lumina-auto` | Auto care, repair, and towing services |

These names and scopes replace earlier draft labels. A capability may be shared or configurable across verticals, but vertical business rules remain owned by the relevant vertical repository.

## Business-System Integration

The product is headless with respect to the business system of record: Lumina provides operator workflows and orchestration around the authoritative business system. ERPNext is a candidate initial integration, not a required dependency for every vertical. Keep capability contracts provider-neutral, preserve each external system's authority for its data, and place provider-specific mapping and transport behind connector boundaries.

## Operator Experience

### Mobile and tablet shell

- Prioritize fast, touch-first tablet and mobile workflows, with responsive layouts, deliberate dark/light behavior, and targets suitable for one-handed operation.
- Keep the existing React/Tailwind surface. Motion may use a lightweight animation library where it improves feedback; respect reduced-motion preferences and avoid making one animation package part of the platform contract.
- Motion may provide clear transition and acknowledgement cues. Avoid blocking spinners where useful content or a pending state can remain visible.
- Optimistic updates are allowed for local drafts and reversible UI state. Never show a business mutation as complete until the system of record confirms it; offline and retry states must be explicit.

### Gear 1: deterministic operation

- Provide direct operational screens and role-authorized tasks that work without model inference.
- Cash counts, end-of-day till reconciliation, and safe audits use fixed denomination grids and deterministic totals. These flows disable AI, autocomplete, and camera interpretation.
- Preserve actor identity, input provenance, adjustments, and approvals in the existing tamper-evident audit path. Do not describe ordinary UI behavior as cryptographic proof unless it is actually signed and independently verifiable.

### Gear 2: bounded assistance

- Offer contextual drafting and inline suggestions; a local SLM may propose ghost text or calculations for explicit operator acceptance.
- Distinguish deterministic values, external data, and model-generated suggestions in the UI. A Tab/accept action is an explicit user decision, not an authorization to commit a mutation.
- Model output remains a draft until reviewed. Final submission follows the system-of-record, Tool Token, and human-approval boundaries.

### Authentication and employee identification

- Support an extensible fast-auth surface for PIN and, where the target device/browser supports it, NFC employee passes and QR passes.
- A four-digit PIN grid may submit on the final digit without an Enter button, with clear lockout feedback and server-side throttling.
- A prompted front-camera scan may read a signed employee wallet QR; NFC NDEF passes are available only on supported hardware and browser/native runtimes.
- Passes must be signed or server-validated, revocable, scoped, and protected against replay; PINs require throttling and secure verification.
- Camera scanning must be user-visible and permission-bound. Do not run continuous camera capture by default.
- BLE proximity may select or prefill an employee prompt, but is not an authenticator and must not unlock an account or authorize an action by itself.
- Validate browser, operating-system, and hardware support before promising NFC or background scanning. A native wrapper or dedicated gateway may be required.

### Tasks and proof of work

- Provide a shared task surface with server-authorized role filtering and explicit task ownership/status transitions.
- Swipe-to-complete may accelerate reversible task acknowledgement, with an accessible button/keyboard alternative; it must not silently authorize a financial or irreversible mutation.
- Camera evidence may be attached to a task when permitted. VLM output is an advisory classification with confidence and provenance, not sole proof of compliance or a substitute for human escalation.
- Define consent, retention, access, and deletion policies for images; do not retain them as raw conversation or general institutional memory.

## IoT and Edge Telemetry

- Tablets may act as BLE gateways on supported platforms, with a dedicated edge gateway as an alternative. Background scanning is platform- and permission-dependent; the web UI must not promise silent continuous collection.
- Sensor payloads include device identity, measurement, unit, timestamp, calibration/provenance, and integrity metadata. Gateways buffer and deduplicate readings and expose queued, delivered, stale, and failed states.
- Readings are sent through an authenticated connector to the configured system of record. ERPNext is one possible target; hard-coded ERPNext posting does not belong in the shared business core.
- Stale-reading windows, such as a 120-minute cooler example, are per-sensor configuration, not universal constants. Notify eligible roles using current server-authorized assignments; do not continuously track employee location.
- Use standard IP-based ESC/POS where supported. Cash-drawer kick signals and other physical interfaces require a compatible printer or edge gateway; a tablet must not be assumed to provide a direct RJ11 interface.

## Operational Rules and Evidence

### Demand and prep planning

Historical transactions, local event calendars, and weather feeds may inform demand forecasts and prep suggestions. Keep the forecast method, data sources, timestamp, confidence, and fallback policy visible. Weather and calendar feeds are uncertain external inputs, not Domain Physics. Deterministic policy may apply approved thresholds to a forecast, while the operator reviews material prep or purchasing changes.

### DSD invoices and receiving

VLM/OCR may propose invoice fields, line items, deposits/CRV, credits, and stales from a supplier document. Preserve source evidence and field-level confidence, reconcile totals, flag ambiguity, and stage a draft for authorized review. No model extraction writes directly to the system of record or posts a payable without the established approval and idempotency controls.

### Cash cohorts, tips, and treasury

Configured shift cohorts may lock tip-pool calculation until every assigned server has reconciled a till or an authorized exception is recorded. Payroll, tip distribution, safe thresholds, and cash-versus-digital payout rules are jurisdiction- and policy-sensitive. Encode approved rules as versioned configuration, surface missing or conflicting tills, and require authorized review before payout. A low safe balance must not silently redirect wages or tips to another payment channel.

### Maintenance and vendor work

Maintenance frequencies are configurable by vertical, site, equipment, and operating conditions (for example, a site may schedule FOH sweeping twice daily or a grease trap every 30 days). The task service schedules work and records completion evidence. Vendor invoices may use the same staged document-intake process; extracted data remains a proposal until reconciled and approved.

## Product Delivery Boundaries

- Shared interaction shells, task mechanics, identity/authorization hooks, telemetry envelopes, connector contracts, and audit behavior belong in `lumina-biz` when reusable across verticals.
- Vertical terminology, physics, workflows, demand rules, units, hardware profiles, and provider mappings belong in the corresponding public vertical repository unless demonstrably generic.
- Customer credentials, operational records, legal/payroll configuration, and deployment secrets stay in private customer systems and secret stores, not public source repositories.
- Every vertical and customer fork records its upstream tag/commit and tests compatibility when syncing updates.

## Open Decisions Before Runtime Commitment

- Select the first supported tablet/browser and whether NFC/BLE requires a native wrapper or dedicated edge gateway.
- Define pass issuance, revocation, offline authentication, and device-loss recovery.
- Select sensor identity, calibration, integrity, and retry protocols.
- Choose the initial F&B system-of-record adapter while retaining provider-neutral capability contracts.
- Obtain jurisdiction-specific policy review for cash controls, tip pooling, payroll fallback, image capture, and employee notifications.
- Define retention and consent policies for proof-of-work images and sensor/employee association.
- Establish hardware certification profiles for printers and cash-drawer interfaces.

These decisions are prerequisites for detailed runtime acceptance criteria; they are not reasons to stall provider-neutral contracts or UI prototypes that can already be tested safely.
