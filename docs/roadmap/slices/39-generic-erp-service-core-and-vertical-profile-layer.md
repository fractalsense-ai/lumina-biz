---
title: "Slice 39 — Generic ERP Service Core and Vertical Profile Layer"
slice: 39
status: planned
version: 0.2.0
last_updated: 2026-08-06
---

## Purpose

Lock the reusable ERP integration direction by defining one canonical service workflow core that supports multiple vertical presentations (for example towing and retail-delivery) without forcing core runtime changes.

## Scope

- Define profile-driven vertical variation over a shared canonical service operation graph.
- Keep canonical capability namespaces and action classes stable across profiles.
- Isolate ERP provider specifics to thin mapping adapters.
- Define optional low-change customization hooks (for example custom doctype/table mappings) that do not alter canonical contracts.
- Define parity expectations across at least ERPNext and Odoo for identical canonical operations.

## Out of Scope

- Rewriting core engine flow in `src/lumina/`.
- Provider-specific schema promotion into canonical request/result contracts.
- Full provider feature parity across all ERP modules.

## Required Changes

- Add profile contract documentation for vertical presentation/configuration overlays.
- Add mapping-boundary guidance for provider-specific object translation.
- Add portability/conformance scenarios for at least towing and retail-delivery profiles.
- Add evidence requirements showing cross-provider canonical parity.
- Define temporary delivery protocol requiring local full-workflow CI parity checks before merge while hosted GitHub CI is unstable.

## New/Changed Contracts

- New profile contract: `service_vertical_profile_v1`.
- New mapping-extension contract: `provider_custom_mapping_hook_v1`.
- Extended portability evidence requirement over existing connector conformance artifacts.

## Files Likely Touched

- `docs/7-concepts/business-system-capability-taxonomy.md`
- `docs/7-concepts/domain-adapter-pattern.md`
- `src/lumina/business_ops/connectors/*/mapping.py`
- `src/lumina/business_ops/connectors/conformance.py`
- `src/lumina/business_ops/replay.py`
- `tests/test_connector_*_manifest.py`
- `tests/test_business_ops_replay_service.py`
- `docs/roadmap/slices/39-generic-erp-service-core-and-vertical-profile-layer.md`

## Acceptance Criteria

- A single canonical service action graph supports both towing and retail-delivery profile variants.
- Profile differences are limited to configuration/presentation overlays and do not change canonical payload shape.
- ERPNext and Odoo both pass shared conformance and replay parity scenarios for both profiles.
- Optional provider customization path (for example custom doctype mapping) is demonstrated without changing canonical contracts.

## Tests

- Cross-profile conformance suite for canonical service actions.
- Cross-provider replay parity suite for towing and retail-delivery profiles.
- Negative tests proving profile-specific fields are rejected from canonical payload keys.
- Temporary local CI-fallback parity validation before merge.

## Delivery Protocol (Temporary CI Fallback)

Until hosted GitHub CI stability is restored, every Slice 39 PR MUST run a local
full-workflow gate before merge.

Required command sequence:

- Optional local services (when scenario coverage needs compose-backed stack):
	- `docker compose -f hermesport/docker-compose.yml up -d`
- Full verification harness:
	- `./scripts/run-full-verification.ps1`
- Backend CI-parity coverage gate:
	- `.venv/Scripts/python.exe -m pytest tests -q --cov=lumina --cov-report=term-missing --cov-fail-under=85`
- Frontend CI-parity gates:
	- `cd src/web`
	- `npm ci`
	- `npm run test:unit`
	- `npm run test:coverage`
	- `npm exec playwright install chromium`
	- `npm run test:e2e`

Required PR evidence while this protocol is active:

- Commands executed (exact command lines).
- Pass/fail outcomes for each gate.
- Runtime note indicating whether compose-backed services were used.

### Sunset Rule

This temporary fallback protocol is removed only after GitHub Actions CI shows
5 consecutive green runs on `main` for the core `CI Tests` workflow.

Sunset proof requirements:

- Link the 5 consecutive successful workflow runs.
- Include run timestamps.
- Record the sunset note in roadmap docs before removing protocol language.

If CI regresses after sunset, this protocol can be re-enabled with a roadmap
note update.

## Ledger/Governance Impact

- Keeps multi-vertical ERP integration decisions auditable and contract-driven.
- Prevents uncontrolled drift into provider- or vertical-specific forks of core runtime semantics.

## Follow-Up Slices

- Slice 36 execution and hardening must preserve this slice's invariants.
- Future vertical slices should extend profile overlays before proposing core workflow changes.

## Implementation-Ready PR Description Template

### Title

Slice 39: generic ERP service core with profile-layer variance

### PR Scope

- Introduce/clarify canonical service-core plus profile-layer contracts.
- Add mapping-boundary and low-change customization guidance.
- Add cross-provider and cross-profile parity evidence.

### Acceptance Criteria

- Canonical action graph parity is proven across target profiles/providers.
- Provider customization path is low-change and contract-safe.
- No core-engine fork is required for vertical variation.

### Test Checklist

- [ ] `./scripts/run-full-verification.ps1`
- [ ] `.venv/Scripts/python.exe -m pytest tests -q --cov=lumina --cov-report=term-missing --cov-fail-under=85`
- [ ] `cd src/web && npm ci && npm run test:unit && npm run test:coverage && npm exec playwright install chromium && npm run test:e2e`
- [ ] `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
- [ ] `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

### Out of Scope Confirmations

- No broad ERP feature-completeness work in this slice.
- No auth transition implementation from Slice 37/38 in this slice.
