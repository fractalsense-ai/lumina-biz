---
version: 1.4.1
last_updated: 2026-08-04
---

# Domain Adapter Pattern

**Version:** 1.4.1  
**Status:** Active  
**Last updated:** 2026-08-04  

---

This document explains how domain packs extend the core engine's behaviour without modifying it. It is the canonical reference for any author adding computed signals, NLP pre-processing, or multi-step task logic to a new domain pack.

---

## A. The Engine Contract

The core engine (`src/lumina/api/processing.py`) reads a small set of **well-known generic fields** from `turn_data` after each turn. These fields are called **engine contract fields**. The engine never inspects domain-specific field names.

This is the hard invariant:

> **Zero domain-specific names may appear in `src/lumina/`.** All domain logic, domain field names, and domain computations live exclusively in the domain pack.

What varies completely between domains is *how* the runtime adapter computes those contract fields. A service workflow adapter might say "the current node is ready when intake completeness and approval checks pass." A manufacturing adapter might say "the current node is ready when required checkpoints for this step are complete." The host sees only generic synthesized signals — the reasoning stays in the domain pack.

---

## B. Engine Contract Field Reference

These are the fields the core engine reads by name from `turn_data`. Every domain pack that wants the associated engine behaviour must populate them in its runtime adapter.

| Field | Type | Default | What the engine does with it |
|---|---|---|---|
| `task_ready_for_execution` | `bool` | `false` | Reserved readiness signal for task/node advancement. Domain packs and hooks may consume it; core runtime consumption is optional and version-dependent. |
| `task_status` | `str` | `""` | When non-empty, writes to `current_task["status"]` — lets the adapter tag the running lifecycle state of the current task (e.g. `"intake_complete"`, `"awaiting_approval"`) |

### Scope note: node readiness vs workflow completion

`task_ready_for_execution` is a **node/task readiness** signal, not a whole-workflow completion signal.

- In DAG-driven domains, dependency checks (`depends_on`, topological scheduling, ready-node selection) remain inside the domain pack's orchestration logic.
- The host/core runtime does not need DAG internals. It consumes generic turn signals only.
- If a domain needs a distinct terminal indicator (for example `workflow_complete`), that indicator is domain-owned and separate from `task_ready_for_execution`.

### Usage pattern

These two fields are complementary for multi-step tasks. On each turn the adapter sets `task_status` to a progress marker. When the current node/task has sufficient prerequisites, it may also set `task_ready_for_execution = True` as a domain-owned readiness signal.

**Business Ops example** — intake and approval verification:
```python
evidence["task_ready_for_execution"] = (
    evidence.get("intake_complete") is True
    and evidence.get("explicit_approval_language") is True
    and evidence.get("confidence_score", 0.0) >= evidence.get("approval_threshold", 0.6)
)
```

**Hypothetical mass-spec example** — 15-step procedural task:
```python
steps_done = evidence.get("verified_step_count", 0)
evidence["task_status"] = f"step_{steps_done}_of_15_complete"
evidence["task_ready_for_execution"] = steps_done >= 15
```

Both examples live entirely in their respective domain packs. The engine sees the same two field names regardless of domain.

### Missing-information path

If prerequisites are missing, domains should route to bounded information acquisition rather than dead-end blocking:

- ask actor for required fields,
- retrieve from external business system via approved connector/tool,
- retrieve scoped institutional memory evidence.

This keeps DAG/task flow moving without exposing DAG internals to the host.

---

## C. The Four-Layer Distinction

Domain packs are authors of four distinct types of components. These are often confused; understanding the distinction is essential before writing a runtime adapter.

### 1. Tool Adapters (`controllers/tool_adapters.py` or `modules/<module>/tool-adapters/`)

**Active verifiers** that produce structured data on demand. There are two kinds:

- **Policy-driven tool adapters** — declared in YAML under `modules/<module>/tool-adapters/` and registered in `cfg/runtime-config.yaml` under `tool_call_policies`. Called by the core engine's policy system (`apply_tool_call_policy`) on specific resolved actions.
- **Direct tool adapters** — defined in `controllers/tool_adapters.py` and registered in `cfg/runtime-config.yaml` under `adapters.tools`. Called directly by the runtime adapter (or by operator tooling) rather than by the orchestrator's policy system. Used for read-only data retrieval where policy-level gating is unnecessary.

In both cases:
- Should be **pure and deterministic**: same inputs → same outputs
- Must take `payload: dict` and return `dict`
- Must not import from `src/lumina/` (keeps the domain pack self-contained)

### 2. Domain Library (`domain-lib/`)

**Passive state estimators** that track entity state across turns — e.g., progression monitor, consistency tracker, stability model. They are implemented as Python classes/functions and called **inside the runtime adapter** (`domain_step` in `runtime_adapters.py`). They are never called directly by the core engine.

- Specifications live in `domain-lib/*.md`
- Implementations live in `controllers/*.py`
- Called **by the runtime adapter**, not the orchestrator
- Produce state transitions (e.g., fluency `advanced: True`) that the adapter then uses to populate engine contract fields

### 3. Runtime Adapter (`controllers/runtime_adapters.py`)

The **synthesis layer** — the domain pack's primary integration point with the core engine. It owns two phases of work on every turn:

- **Phase A:** NLP pre-processing (before the LLM turn)
- **Phase B:** Signal synthesis (after all tool and domain-lib results are in)

The adapter can call into domain-lib components and invoke tool functions directly (not via policy). Its output is the `evidence` dict, which the engine reads for invariant evaluation, action resolution, and engine contract field consumption.

### 4. Group Libraries and Group Tools (`domain-lib/*.py` and `controllers/group_tool_adapters.py`)

**Domain-scoped shared resources** used by multiple modules within the same domain pack. Group Libraries are passive pure-function modules (sensor normalisation, anomaly detection). Group Tools are active shared verifiers following the same `payload: dict → dict` contract as tool adapters.

Both are declared in the module's `domain-physics.json` under `group_libraries` and `group_tools` arrays, discovered by `adapter_indexer.scan_group_resources()` at startup, and stored in the runtime context. The route compiler validates their references at compile time.

For the complete reference on declaration format, resolution pipeline, and the business-ops reference implementation, see [`group-libraries-and-tools(7)`](group-libraries-and-tools.md).

---

## D. Phase A — NLP Pre-Processing

Phase A runs on the raw user message **before** the LLM prompt is assembled. Its job is to extract deterministic structured signals from unstructured text and inject them as grounding anchors into the LLM prompt context — making turn interpretation more reliable and reducing LLM hallucination of factual fields.

The NLP pre-interpreter is registered at startup via `cfg/runtime-config.yaml`:

```yaml
nlp_pre_interpreter_fn: nlp_preprocess   # function in controllers/nlp_pre_interpreter.py
```

And called from the main server via `runtime.get("nlp_pre_interpreter_fn")` before passing control to `interpreter(**kwargs)` in `runtime_adapters.interpret_turn_input`.

### What the business-ops pre-interpreter extracts

| Extractor | Output fields | Method |
|---|---|---|
| `extract_risk_markers` | `contains_high_risk_terms`, `risk_markers` | Keyword regex and policy phrase matching |
| `extract_approval_language` | `explicit_approval_language` | Keyword regex for explicit approval intents |
| `extract_intake_completeness` | `intake_complete`, `missing_fields` | Deterministic payload/intake field checks |
| `extract_workflow_focus_ratio` | `off_workflow_ratio` | Workflow vocabulary overlap as a ratio of total tokens |

Extracted values are returned as a partial `evidence` dict plus a `_nlp_anchors` metadata list. The anchors are formatted into natural-language lines and prepended to the LLM context hint, tagged as deterministic:

```
NLP pre-analysis (deterministic):
- intake_complete: true
- explicit_approval_language: true
- off_workflow_ratio: 0.1
Use these as starting values. Override if your analysis disagrees.
```

The LLM may override them, but having deterministic anchors as a prior makes overrides the exception rather than the rule.

### Adding a new Phase A extractor

1. Write a pure function in your domain's `controllers/nlp_pre_interpreter.py` that takes `input_text: str` and returns a `dict`.
2. Call it inside `nlp_preprocess()` and add the result to `evidence` and `anchors`.
3. Register the output field in `cfg/runtime-config.yaml` under `turn_input_defaults` and `turn_input_schema`.
4. Nothing in `src/lumina/` needs to change.

---

## E. Phase B — Signal Synthesis (Step-by-Step Template)

Phase B runs at the **end of `interpret_turn_input()`**, after the LLM has produced the base evidence dict and after any tool adapter overrides (algebra parser, etc.) have been applied. Its job is to compute engine-contract and domain-owned synthesized signals for downstream orchestration.

### Template for adding a new computed gate signal

**Step 1 — Define the field in `cfg/runtime-config.yaml`**

Add a default and a schema entry:

```yaml
turn_input_defaults:
  my_signal: false           # or "" for string fields

turn_input_schema:
  my_signal:
    type: bool
    default: false
```

**Step 2 — Compute it at the end of `interpret_turn_input()` in `controllers/runtime_adapters.py`**

Place the computation immediately before `return evidence`. Use only fields that already exist in `evidence` — no imports from `src/lumina/`, no hardcoded action names.

```python
# Compute my_signal from domain-owned evidence fields only.
evidence["my_signal"] = (
    evidence.get("some_domain_field") is True
    and evidence.get("step_count", 0) >= evidence.get("required_steps", 1)
)

return evidence
```

**Step 3 — Done. No changes to `src/lumina/`.**

The core engine reads the field by name via `turn_data.get("my_signal")`. If the field name is not yet in the engine contract field reference table above, open a PR to add it — that table is the only coupling point between domain packs and the core engine.

### Annotated reference: `task_ready_for_execution` in an active domain

```python
# At the end of interpret_turn_input() in
# model-packs/business-ops/controllers/runtime_adapters.py

# A task is ready for execution when intake checks and approval checks pass.
# This is a domain-owned readiness signal and must not reference domain
# field names outside this adapter.
evidence["task_ready_for_execution"] = (
    evidence.get("intake_complete") is True
    and evidence.get("explicit_approval_language") is True
    and evidence.get("confidence_score", 0.0) >= evidence.get("approval_threshold", 0.6)
)
```

Workflow thresholds are domain-owned fields set by runtime configuration and carried through `current_task` into evidence defaults. Invariant checks should reference those evidence fields by name, not hardcoded literals. This is also entirely within the domain pack.

---

## F. What NOT To Do

These are the anti-patterns that violate the domain-agnostic invariant. All three have been observed during development and should be caught in code review.

### ❌ Domain field names in `src/lumina/`

```python
# WRONG — in src/lumina/api/
task_ready_for_execution = (
    intake_status == "complete"
    and turn_data.get("approval_check") is True      # ← domain field
    and resolved_action not in {"request_more_info"}  # ← domain standing-order ID
)
```

`approval_check` is a domain field. `request_more_info` is a domain standing-order ID. Neither should appear in the core engine. The correct fix is to move the computation into the adapter (Phase B) and expose only generic synthesized signals to the host.

### ❌ Calling domain-lib directly from the orchestrator

The orchestrator receives a `domain_lib_step_fn` lambda that wraps the domain's `domain_step` function. It calls that lambda — it does not import or call domain progression monitors, consistency trackers, or any other domain-lib component directly.

### ❌ Bypassing the adapter to write gate signals in the server

All synthesized signals must be populated by the domain pack's `interpret_turn_input`. Writing `turn_data["task_ready_for_execution"] = True` anywhere in `processing.py` or in the orchestrator constitutes domain logic in the core and must be moved to the adapter.

---

## G. Slice 39 Profile-Layer Guardrail

For service-like business domains, Slice 39 introduces a mandatory separation between canonical workflow behavior and vertical presentation profiles.

### Rule 1 — Canonical envelopes remain stable

Runtime adapters and connector mappings must continue to exchange canonical payload envelopes for action classes (`query`, `create_draft`, `update_draft`, `request_commit`, etc.).

### Rule 2 — Vertical variation stays in profile/config space

Differences such as towing vs retail-delivery terminology, display priorities, and optional metadata belong in profile-layer configuration, not in core engine fields or provider-specific action classes.

### Rule 3 — Provider specifics stay in mapping adapters

ERPNext/Odoo object names and custom doctype/table wiring are mapping concerns and must remain isolated in connector adapter modules.

### Rule 4 — No profile key leakage into canonical payload keys

Profile-specific keys must be filtered or rejected before canonical mapping functions execute. Mapping tests should enforce this behavior for all supported providers.

---

## Reference: Business Ops Domain Adapter Structure

```
model-packs/business-ops/
├── cfg/
│   └── runtime-config.yaml          ← declares defaults, schema, tool policies
├── domain-lib/
│   └── reference/
│       └── turn-interpretation-spec-v1.md
├── controllers/
│   ├── nlp_pre_interpreter.py       ← Phase A: intent/signal extraction
│   ├── domain_state.py              ← domain-lib state evolution helpers
│   ├── policy_compiler.py           ← standing-order and route synthesis
│   └── runtime_adapters.py          ← Phase A + Phase B synthesis; computes task_ready_for_execution
└── modules/auto-repair/
    └── tool-adapters/
        ├── business-ops-knowledge-hub-v1.yaml
        └── business-ops-journal-v1.yaml
```

---

## Reference: System Domain Adapter Structure

The system domain (`domain/sys/system-core/v1`) serves the special `system` role (root operators). It has no generative task: it is a read-only introspection surface for the Lumina OS runtime itself. This makes it a useful reference for the **minimal viable domain pack** pattern.

```
model-packs/system/
├── cfg/
│   └── runtime-config.yaml          ← local_only: true; slm_weight_overrides;
│                                       adapters.tools; deterministic_templates
└── controllers/
    ├── runtime_adapters.py           ← Phase A + Phase B; populates command_dispatch
    └── tool_adapters.py              ← direct tool adapters (no modules/ layer needed)
```

### `local_only: true`

The system domain sets `local_only: true` in its `runtime-config.yaml`. This flag is propagated by `load_runtime_context()` and causes `process_message()` to route the turn through the SLM rather than the LLM. **An external LLM is never called for system-domain turns** — this enforces a security boundary that prevents operational metadata (session IDs, physics hashes, escalation records) from being sent to third-party inference services.

If the SLM is unavailable, the turn resolves through the domain's `deterministic_templates` in the runtime config. The LLM is not used as a fallback.

```yaml
# model-packs/system/cfg/runtime-config.yaml (excerpt)
local_only: true

deterministic_templates:
  system_command:    "Command received. Processing via system tools."
  system_status:     "System status: all subsystems nominal."
  system_diagnostic: "Diagnostic check complete. No anomalies detected."
  system_general:    "System acknowledged."
```

### No `modules/` layer

The system domain does not use the policy-driven tool adapter pattern. Its tool adapters are direct call adapters registered under `adapters.tools` and called from `interpret_turn_input` when `command_dispatch` carries a known operation name. This is appropriate for domains whose tools are pure read-only queries — no state is mutated, so policy gating adds no value.

### Action codes

The system domain's `system_domain_step` maps `query_type` evidence to six action codes:

| `query_type` | Action code |
|---|---|
| `admin_command` | `system_command` |
| `status_query` | `system_status` |
| `diagnostic` | `system_diagnostic` |
| `config_review` | `system_config_review` |
| `out_of_domain` | `out_of_domain` |
| anything else | `system_general` |

If `command_dispatch` is non-null in evidence (populated by `slm_parse_admin_command`), it overrides the `query_type` mapping and forces `system_command` regardless of the classified type.

---

## SEE ALSO

- [`ai-governance-principles(7)`](ai-governance-principles.md) — deterministic governance constraints implemented by adapter phases
- [`domain-pack-anatomy(7)`](domain-pack-anatomy.md) — seven-component anatomy and file layout
- [`group-libraries-and-tools(7)`](group-libraries-and-tools.md) — Group Libraries and Group Tools declaration, resolution, and examples
- [`execution-route-compilation(7)`](execution-route-compilation.md) — ahead-of-time route compilation from physics pointers (validates tool and library references)
- [`nlp-semantic-router(7)`](nlp-semantic-router.md) — Tier 1 domain classification and Tier 2 NLP pre-interpreter
- [`edge-vectorization(7)`](edge-vectorization.md) — per-domain vector stores built from the same adapter-indexer discovery pass
- [`../../model-packs/business-ops/controllers/runtime_adapters.py`](../../model-packs/business-ops/controllers/runtime_adapters.py) — active domain runtime adapter reference
- [`../../model-packs/system/cfg/runtime-config.yaml`](../../model-packs/system/cfg/runtime-config.yaml) — system-domain admin operations and deterministic command mappings

