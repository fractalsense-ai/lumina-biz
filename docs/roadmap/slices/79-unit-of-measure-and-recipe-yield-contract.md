---
title: "Slice 79 - Unit-of-Measure and Recipe/Yield Contract"
slice: 79
status: planned
version: 1.0.0
last_updated: 2026-11-08
---

## Purpose

Define deterministic unit normalization and reviewed recipe/yield calculations for restaurant inventory and production workflows.

## Scope

- Define canonical units, dimensions, precision, and conversion rules.
- Define recipe and yield inputs, calculation outputs, and provenance.
- Define draft conversion from a recipe into a BOM-ready structure.
- Define human review for uncertain or operationally material conversions.

## Out of Scope

- A complete restaurant inventory or recipe runtime.
- Supplier-specific conversion tables or automatic production execution.
- Direct writes to a system of record without explicit review.

## Required Changes

- Document supported unit conversions and invalid/ambiguous inputs.
- Define yield calculation and rounding semantics.
- Define recipe-to-BOM draft schema and verification evidence.

## New/Changed Contracts

- `uom_normalization_contract_v1`
- `recipe_to_bom_draft_contract_v1`
- `yield_calculation_contract_v1`

## Acceptance Criteria

- Conversions are deterministic, dimensionally valid, and explicit about precision.
- Recipe and yield results retain their source inputs and calculation provenance.
- Ambiguous results are blocked or flagged for review before operational submission.

## Tests

- Review conversion, precision, and ambiguity examples.
- Verify draft schema and review gates.
- Run repo verification and manifest integrity checks.
