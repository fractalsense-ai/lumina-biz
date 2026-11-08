---
title: "Slice 75 - Gear 2 Assistant Drawer and Context-Locking Telemetry"
slice: 75
status: planned
version: 1.0.0
last_updated: 2026-11-08
---

## Purpose

Define the Gear 2 assistant as a contextual drafting sidecar to Gear 1, with explicit context locking, human review, and privacy-safe telemetry.

## Scope

- Define assistant-drawer invocation and active-screen context propagation.
- Define draft-only behavior for forms and operational actions.
- Define telemetry for context source, lock state, model path, and degraded mode.
- Preserve the no-raw-chat-log rule for institutional memory and telemetry.

## Out of Scope

- Restaurant invoice VLM implementation.
- Autonomous submission or mutation by the assistant.
- Storing raw conversation transcripts as operational memory.

## Required Changes

- Specify the drawer/FAB interaction and context lock lifecycle.
- Specify staged draft, evidence display, user review, and explicit submit boundaries.
- Define minimal telemetry fields without transcript content or unnecessary PII.

## New/Changed Contracts

- `gear_2_assistant_drawer_v1`
- `screen_context_lock_contract_v1`
- `ui_context_telemetry_v1`

## Acceptance Criteria

- Gear 2 cannot act without the authorized screen context and Tool Token.
- Model output remains a draft until a human reviews and confirms it.
- Telemetry records control/evidence metadata without raw chat content.
- Loss of context fails closed or returns to the deterministic Gear 1 surface.

## Tests

- Review context lock, expiry, and screen-switch scenarios.
- Review telemetry fields for transcript and PII exclusion.
- Run repo verification and manifest integrity checks.
