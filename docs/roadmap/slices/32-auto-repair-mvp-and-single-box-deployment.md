---
title: "Slice 32 — Auto Repair MVP and Single-Box Deployment Topology"
slice: 32
status: delivered
version: 1.0.0
last_updated: 2026-08-01
---

# Slice 32 — Business Ops Pack Bootstrap

## Purpose

Define the first vertical implementation (independent auto repair) and the local-first single-box deployment model that combines ERPNext + Lumina institutional memory + bounded agentic tooling.

## Scope

- Define auto-repair MVP module workflows:
Bootstrap a reusable business-operations model pack (from template patterns) that binds actor model, scoped institutional memory, connector routing, and bounded governance behavior.
  - precedent-assisted technician support,
  - bounded escalation to owner/manager approval,
  - ERP draft updates through adapters.
- Define business-ops pack skeleton (manifest, runtime config, domain physics, profiles, role map).
- Define actor types and groups suitable for SMB operations contexts.
- Define initial operation categories and bounded standing orders.
- Define module extension posture for verticals (auto repair first, others later).

- General availability hardening for all verticals.
- Full POS and restaurant implementation.
- Full multi-vertical implementation.
- Production UI polish.
- Billing/commercial packaging logic.

- Add auto-repair module slice spec with actor flows and operation boundaries.
- Add deployment architecture note for local server + VPN-based multi-site access.
- Create business-ops pack slice spec aligned with template pack anatomy.
- Define module-map strategy and role/permission model.
- Define domain profile extension fields required by institutional memory and external-system references.

- New auto-repair module contract for task/event shapes.
- New deployment contract for local-first runtime assumptions:
- New `business-ops` domain-pack contract (pack identity + module boundaries).
- New role and actor contracts for owner/manager/operator/front-desk/customer-intake contexts.
- New profile extension contract including organization/site defaults and memory policy flags.
- New E2E fixture contract linking thread routing, precedent scoring, and ERP operation replay.

## Files Likely Touched
- `model-packs/template/**` (as source patterns)
- `docs/7-concepts/domain-pack-anatomy.md`
- `tests/test_*business_ops*` (new)
- `tests/test_*business_ops*` (new)
- `tests/test_*erpnext*` (expanded)
- `docs/roadmap/slices/32-auto-repair-mvp-and-single-box-deployment.md`

- Pack scaffold follows HMVC and runtime adapter contract patterns already used in framework.
- Actor, role, and profile contracts align with scoped memory and connector requirements.
- Governance boundaries stay consistent with System Pack authority model.
  - precedent retrieval -> confidence-scored recommendation,
  - high-risk case -> escalation packet,
  - approval -> bounded ERP draft mutation.
- Structural pack tests (manifest/runtime-config/domain-physics shape).
- Role/permission contract tests.
- Profile merge tests for base/domain/role composition.
## Tests

- Deterministic integration tests with fixture replay only.
- Introduces business-domain governance semantics without changing system authority ownership.
- Ensures all bounded operations remain traceable through existing audit model.

## Ledger/Governance Impact

- Slice 33: ERPNext reference connector and deterministic fixtures.
- Slice 34: secondary provider connector and conformance harness.
- Maintains authority boundaries: recommendations and staging remain separate from final governance approvals.

## Follow-Up Slices

- Operational hardening slices (performance, backup/restore, disaster recovery).
- Additional vertical module slices (restaurant/POS, light manufacturing, service ops).

## Implementation-Ready PR Description Template

### Title

Slice 32: Business Ops pack bootstrap and auto-repair MVP boundaries

### PR Scope

- Bootstrap a reusable `business-ops` model pack scaffold aligned with template pack anatomy.
- Define bounded auto-repair module workflows (recommendation, escalation, staged mutation).
- Define actor/role/profile extension contracts for SMB operating contexts.
- Define local-first single-box deployment assumptions and boundaries.

### Acceptance Criteria

- Pack scaffold matches framework HMVC/runtime conventions and validates structurally.
- Actor, role, and profile contracts merge deterministically across base/domain/role layers.
- Auto-repair bounded flow is represented in fixtures and replayable without side effects.
- Governance boundaries remain unchanged: no direct commit authority is introduced.

### Test Checklist

- [x] Structural pack tests for manifest/runtime/domain-physics shapes.
- [x] Role and permission contract tests for business-ops actors.
- [x] Profile merge/composition tests for base/domain/role overlays.
- [x] Deterministic fixture replay tests for recommendation, escalation, and staged ERP mutation.
- [x] Governance regression checks ensuring no authority-boundary drift.

### Out of Scope Confirmations

- No production UI polish or commercial packaging logic.
- No provider-specific execution client beyond bounded staging interfaces.
- No distributed transaction orchestration.

## Delivery Evidence

- Pack scaffold delivered under `model-packs/business-ops/` with runtime config, role map, profile extension, adapters, and auto-repair module contracts.
- Structural and contract validation tests delivered in `tests/test_business_ops_pack.py`.
- Verification run:

```bash
python -m pytest tests/test_business_ops_pack.py -q
```

- Result on 2026-08-01: `14 passed`.
