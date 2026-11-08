---
title: "Slice 80 - Neurosymbolic Compute Cascade Contract"
slice: 80
status: planned
version: 1.0.0
last_updated: 2026-11-08
---

## Purpose

Define deterministic ordering and evidence flow across the business compute cascade before any high-cost or high-capability model call.

## Scope

- Define deterministic text/entity triage and glossary-based intent routing.
- Define bounded structured interpretation and candidate selection.
- Define conditions for escalation to heavy LLM or VLM work.
- Define confidence, degraded-mode, and audit evidence requirements.

## Out of Scope

- Selecting a vendor-specific model as a permanent dependency.
- Replacing the existing orchestration runtime in this documentation slice.
- Allowing model output to bypass Tool Token permissions or human mutation gates.

## Required Changes

- Define stage contracts, inputs, outputs, timeouts, and fallback behavior.
- Distinguish deterministic evidence from model-generated hypotheses.
- Specify how routing and escalation are recorded without persisting raw chats.

## New/Changed Contracts

- `neurosymbolic_compute_cascade_v1`
- `cascade_escalation_policy_v1`
- `cascade_evidence_provenance_v1`

## Acceptance Criteria

- Stage order and transition conditions are deterministic and testable.
- Heavy model use requires a bounded task and sufficient preceding evidence.
- Degraded-mode behavior is explicit and fail-safe.
- Audit records capture decision metadata without raw conversation persistence.

## Tests

- Review normal, low-confidence, timeout, and unavailable-model flows.
- Check consistency with actor authentication, Tool Token, and PPA ordering.
- Run repo verification and manifest integrity checks.
