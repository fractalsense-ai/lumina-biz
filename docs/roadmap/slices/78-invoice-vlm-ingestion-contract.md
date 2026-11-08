---
title: "Slice 78 - Invoice VLM Ingestion Contract"
slice: 78
status: planned
version: 1.0.0
last_updated: 2026-11-08
---

## Purpose

Define the provider-neutral, local-first contract for restaurant invoice ingestion and its reviewed handoff to receiving or back-office systems.

## Scope

- Define document intake, extraction fields, confidence, provenance, and validation.
- Define line-item, quantity, unit, tax, total, and supplier evidence requirements.
- Define anomaly and price-change flags as review signals, not automatic decisions.
- Define local processing defaults and explicit cloud opt-in for heavier inference.

## Out of Scope

- Full invoice runtime, OCR/VLM provider selection, or live ERP mutation.
- Payment processing or automatic supplier approval.
- Customer-specific supplier schemas.

## Required Changes

- Specify the invoice document and extracted-line-item contract.
- Define quality thresholds, unresolved-field behavior, and human review.
- Define the staged draft and API handoff into the restaurant workflow.

## New/Changed Contracts

- `invoice_vlm_ingestion_contract_v1`
- `invoice_line_item_extraction_contract_v1`
- `invoice_anomaly_review_contract_v1`

## Acceptance Criteria

- Extraction output is provider-neutral, traceable to source evidence, and confidence-aware.
- Local-first behavior and cloud opt-in are explicit.
- Anomalies require review and no mutation occurs before authorized approval.

## Tests

- Review representative invoice fixtures and low-confidence cases.
- Verify privacy, evidence, and staged-mutation boundaries.
- Run repo verification and manifest integrity checks.
