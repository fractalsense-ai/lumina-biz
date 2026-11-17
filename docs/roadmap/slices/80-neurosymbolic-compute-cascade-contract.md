---
title: "Slice 80 - Neurosymbolic Compute Cascade Contract"
slice: 80
status: planned
version: 1.0.0
last_updated: 2026-11-17
---

## Purpose

Define deterministic ordering and evidence flow across the business compute cascade before any high-cost or high-capability model call.

## Scope

- Define deterministic text/entity triage and glossary-based intent routing.
- Define bounded structured interpretation and candidate selection.
- Define workflow- and modality-aware selection from approved model capabilities, including text, vision/image and document understanding, speech recognition, and text-to-speech.
- Define safe composition of multiple modalities and conditions for escalation to stronger LLM, VLM, or audio-model work.
- Define confidence, degraded-mode, and audit evidence requirements.
- Define source authority, freshness, revalidation, and retrieval invalidation behavior.
- Define how reviewed outcomes become privacy-limited evaluation or training examples.

## Out of Scope

- Selecting a vendor-specific model as a permanent dependency.
- Replacing the existing orchestration runtime in this documentation slice.
- Using the Coding Agent pack as a product workflow or as the implementation dependency for business model routing.
- Persisting raw chat transcripts or performing automatic online model training.
- Allowing model output to bypass Tool Token permissions or human mutation gates.

## Required Changes

- Define stage contracts, inputs, outputs, timeouts, and fallback behavior.
- Define model capability profiles, including accepted input and produced output modalities, and deterministic selection using task purpose, quality requirements, data sensitivity, device support, availability, latency, and cost.
- Require workflows to declare needed modalities and permissions; unsupported or denied modalities must fall back to an accessible deterministic or text-only path.
- Distinguish deterministic evidence from model-generated hypotheses.
- Specify privacy-safe routing, escalation, source-version, and outcome evidence without persisting raw chats or chain-of-thought.
- Separate authoritative knowledge refresh from model improvement: version sources, define freshness rules, detect changes, and revalidate or invalidate derived retrieval artifacts.
- Define a reviewed, structured outcome-example contract for offline evaluation and controlled training; require purpose limitation, data minimization, versioned datasets, evaluation gates, and rollback.
- Keep transactional state in its system of record and institutional procedures in the knowledge store; neither becomes an unreviewed model-generated fact.

## New/Changed Contracts

- `neurosymbolic_compute_cascade_v1`
- `cascade_escalation_policy_v1`
- `cascade_evidence_provenance_v1`
- `model_capability_profile_v1`
- `model_selection_policy_v1`
- `workflow_modality_requirements_v1`
- `knowledge_source_freshness_v1`
- `curated_outcome_example_v1`

## Acceptance Criteria

- Stage order and transition conditions are deterministic and testable.
- Each workflow selects only from approved model profiles compatible with its purpose, required input/output modalities, data policy, device support, and operational constraints.
- Vision and audio use is permission-bound, reports confidence/provenance where applicable, and has a usable non-modal or text fallback.
- Heavy model use requires a bounded task and sufficient preceding evidence.
- Degraded-mode behavior is explicit and fail-safe.
- Strong-model output remains a hypothesis or draft until checked; it cannot authorize a system-of-record mutation.
- Evidence identifies model, prompt/policy, and source versions plus the reason for escalation, without raw conversation or chain-of-thought persistence.
- Only reviewed, purpose-approved structured outcomes enter offline evaluation or training sets; promotion requires evaluation and rollback gates.
- Source changes trigger configured revalidation or invalidation, and stale knowledge is surfaced rather than silently treated as current.

## Tests

- Review normal, low-confidence, timeout, and unavailable-model flows.
- Test workflow-to-model selection across capability, privacy, latency, cost, and availability constraints.
- Test vision/image-document, speech-input, and text-to-speech selection, multimodal combinations, permission denial, unsupported hardware, and modality-specific fallback.
- Test escalation evidence, human review, curated-example eligibility, and rejection of raw transcript persistence.
- Test source version changes, freshness expiry, revalidation, and retrieval invalidation.
- Check consistency with actor authentication, Tool Token, and PPA ordering.
- Run repo verification and manifest integrity checks.
