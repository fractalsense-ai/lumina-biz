---
title: "Slice 74 - Dual-Mode UI Shell and Gear 1 Deterministic Surface"
slice: 74
status: planned
version: 1.0.0
last_updated: 2026-11-08
---

## Purpose

Define the deterministic, operator-first Gear 1 surface for shared business operations, with AI excluded from authority over structured actions.

## Scope

- Define screen registry and plugin contribution boundaries.
- Define deterministic POS/operator views and permission-aware slash commands.
- Define stable screen and active-context identifiers.
- Define the handoff from deterministic workflows to AI-assisted drafting.

## Out of Scope

- Gear 2 assistant runtime implementation.
- Restaurant-only screens or workflows in `lumina-biz`.
- Automatic submission of business mutations.

## Required Changes

- Document the Gear 1 UI, command, authority, and screen-context contracts.
- Define deterministic behavior when a command is invalid or unauthorized.
- Require human confirmation before mutating submissions.

## New/Changed Contracts

- `gear_1_deterministic_surface_v1`
- `business_screen_registry_v1`
- `slash_command_contract_v1`
- `screen_context_id_contract_v1`

## Acceptance Criteria

- Gear 1 is usable without an LLM call.
- Commands have explicit authorization and deterministic validation behavior.
- AI handoff is scoped to an active screen context and cannot submit mutations by itself.
- Shared UI contracts do not encode restaurant-specific workflows.

## Tests

- Review command authority and screen-context scenarios.
- Link-check referenced UI surfaces.
- Run repo verification and manifest integrity checks.
