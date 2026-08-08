---
title: "Slice 48 - Production Cutover Gates and Rollback Automation"
slice: 48
status: planned
version: 0.1.0
last_updated: 2026-08-08
---

## Purpose

Define and implement production cutover gate policy for ERP execution,
including shadow, canary, and full mutation enablement with rollback automation.

## Scope

- Define measurable gate criteria for shadow, canary, and full mutation phases.
- Define automated rollback trigger thresholds and ownership.
- Define rollout telemetry requirements and release evidence package.
- Define safe feature-flag progression strategy for mutation endpoints.

## Out of Scope

- Secondary provider parity implementation.
- Final governance closeout across all providers.

## Required Changes

- Add cutover gate policy contract.
- Add rollback trigger contract and automated response requirements.
- Add release evidence requirements for go-live decisions.

## New/Changed Contracts

- New: `erp_cutover_gate_policy_v1`.
- New: `erp_rollback_trigger_contract_v1`.
- New: `mutation_feature_flag_progression_policy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/48-production-cutover-gates-and-rollback-automation.md`
- `docs/8-admin/*`
- `src/lumina/system_log/*`
- `src/lumina/services/*`

## Acceptance Criteria

- Shadow/canary/full gates have explicit measurable pass/fail criteria.
- Rollback triggers and automation behavior are explicit and test-covered.
- Mutation enablement remains feature-flag controlled until gates pass.

## Tests

- Gate progression simulation tests (shadow -> canary -> full).
- Rollback trigger and automation tests.
- Feature-flag progression safety tests.
- Integrity checks:
  - `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
  - `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Makes go-live decisions auditable and reversible.
- Reduces uncontrolled risk during mutation activation.

## Follow-Up Slices

- Slice 50.

## Implementation-Ready PR Description Template

### Title

Slice 48: production cutover gates and rollback automation

### PR Scope

- Define and implement cutover gate criteria and rollback automation.
- Add rollout evidence requirements and mutation feature-flag policy.

### Acceptance Criteria

- Gate and rollback contracts are explicit and test-covered.
- Mutation activation remains gated and auditable.

### Test Checklist

- [ ] Gate progression simulation tests.
- [ ] Rollback trigger automation tests.
- [ ] Mutation feature-flag progression tests.
- [ ] `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
- [ ] `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`

### Out of Scope Confirmations

- [ ] No secondary provider parity implementation in this slice.
