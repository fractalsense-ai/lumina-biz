---
title: "Architecture Coherence Gap Register"
status: active
version: 0.1.0
last_updated: 2026-08-06
---

## Purpose

Track architecture-to-runtime enforcement gaps against the Lumina target shape
and map each gap to a dependency-DAG node, owner hotspot, and closure evidence.

## Gap Inventory

| Gap ID | Gap Summary | Risk | Primary Hotspots |
|---|---|---|---|
| G1 | Tool-token boundary is not yet explicit end-to-end at runtime invocation surface | high | `src/lumina/api/dependencies.py`, `src/lumina/api/runtime_helpers.py` |
| G2 | Institutional-memory ingest lacks explicit rejection for chat/conversation payload classes | high | `src/lumina/retrieval/institutional.py` |
| G3 | Pipeline ordering is documented but not uniformly hard-failed/degraded when stages are missing or reordered | high | `src/lumina/api/processing.py` |
| G4 | Cross-domain API-only boundary is partial policy-level, not fully runtime-enforced | high | `src/lumina/daemon/cross_domain.py`, `src/lumina/daemon/task_adapter.py` |
| G5 | Daemon audit-commit coverage parity is not consistently guaranteed | medium | `src/lumina/orchestrator/system_log_writer.py`, daemon task paths |
| G6 | Active SoR actor-liveness verification is not first-class in auth flow | medium | `src/lumina/auth/operating_context.py`, auth dependencies |

## DAG Node Mapping

| Node | Covers Gaps | Depends On | Unblock Criteria |
|---|---|---|---|
| N1 | G1 | none | unauthorized tools structurally excluded and tested |
| N2 | G2 | none | conversation/chat-like record classes rejected at ingest with deterministic error |
| N3 | G3 | none | ordering guards active or explicit degraded-mode telemetry emitted |
| N4 | G4 | N1 | direct cross-domain state access blocked outside API pathways |
| N5 | G5 | N1, N3 | daemon operations must satisfy audit-commit parity gates |
| N6 | G6 | N1, N2 | SoR liveness check policy implemented with deterministic fallback modes |

## Closure Evidence Requirements

For each node closure PR:

- Explicit runtime guard implementation references.
- Positive and negative deterministic tests.
- Failure-mode taxonomy mapped to expected deny/degrade behavior.
- Pseudonymous observability output proving guard activation.
- Rollback criteria for unexpected runtime regressions.

## Verification Commands

- `scripts/manifest-regenerate.ps1`
- `.venv/Scripts/python.exe -m lumina.systools.manifest_integrity check`
- `.venv/Scripts/python.exe -m lumina.systools.verify_repo`
- Local CI fallback evidence per active Slice 39 protocol.
