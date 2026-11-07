---
version: 1.0.0
last_updated: 2026-11-06
---

# Module Authoring Contract v1

**Status:** Active
**Applies to:** every `model-packs/<domain>/modules/<module>/` artifact set

This document defines the normative contract for a module in Lumina. A module is not a standalone pack; it is the bounded execution unit that sits beneath a domain pack and owns one coherent unit of domain behavior.

A valid module is authorable, reviewable, and reusable because it declares a minimal artifact surface and a deterministic file layout.

## 1. Contract scope

A module is the operational authority boundary for a single behavior family inside a domain pack, such as intake, diagnostics, escalation, or governance. It is responsible for:

- owning its local `domain-physics` contract
- declaring a stable default state and task shape
- exposing its runtime entry points in a predictable file layout
- defining deterministic defaults for turn interpretation and task execution
- remaining compatible with the parent domain pack and the framework boundary

The module boundary is intentionally smaller than the pack boundary. The pack defines the domain identity and routing surface; the module defines the behavior contract inside that surface.

## 2. Required module artifact set

Every module should include the following artifacts unless the module intentionally overrides a feature as optional or out-of-scope.

| Artifact | Required | Purpose |
|---|---:|---|
| `module-config.yaml` | Yes | Canonical declaration of the module's runtime identity and default configuration |
| `domain-physics.yaml` | Yes | Human-editable invariant source |
| `domain-physics.json` | Yes | Runtime-ready JSON form used by the loader and validation tools |
| `tool-adapters/` | Recommended | Declarative external-tool contracts used by the module |
| `turn-interpretation-spec` or equivalent module prompt/schema doc | Recommended | Defines the expected interpretation payload for that module |
| `workflows/` or equivalent task flow definitions | Recommended | Optional but preferred for multi-step or reusable operational flows |
| `glossary/` or equivalent vocab bundle | Optional | Localized vocabulary for the module and its domain-specific semantics |

## 3. Required fields in `module-config.yaml`

The `module-config.yaml` file is the approval surface for a module. It must be parseable YAML and should declare the fields below. The repo already has a stable pattern in the template and coding-agent modules, and the contract should preserve that shape rather than invent a different one.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `module_id` | string | Recommended | Stable module identifier for routing, provenance, and tests |
| `module_path` | string | Recommended | Repository-relative module directory path |
| `domain_physics_path` | string | Yes | Relative path to the module's runtime physics file |
| `domain_system_prompt_path` | string | Optional | Module-specific persona or domain prompt when used |
| `turn_interpretation_prompt_path` | string | Optional | Module-specific schema or interpretation guidance |
| `local_only` | boolean | Optional | `true` for local governance/admin-style modules |
| `initial_module_state` | mapping | Yes | Seed state for a new runtime session |
| `default_task_spec` | mapping | Yes | Canonical default task or workflow shape |
| `domain_step_params` | mapping | Yes | Runtime tuning values and constrained defaults |
| `turn_input_defaults` | mapping | Yes | Fallback values that the module expects for turn interpretation |
| `ui_overrides` | mapping | No | Optional branding or presentation overrides |
| `owner` | string | Recommended | Domain owner or authority responsible for the module |
| `version` | string | Recommended | Module version for compatibility tracking |

### Example contract

```yaml
# module-config.yaml
module_id: auto-repair
version: 0.1.0
owner: business-ops

domain_physics_path: model-packs/business-ops/modules/auto-repair/domain-physics.json

initial_module_state:
  open_draft_count: 0
  last_recommendation_tier: null
  turn_count: 0

default_task_spec:
  task_id: auto-repair-intake-001
  operation_category: diagnostics
  nominal_difficulty: 0.45
  connector_capability: erp/work-order

domain_step_params:
  require_manager_approval_for_high_risk: true
  low_confidence_threshold: 0.25
  allowed_workflow_actions:
    - recommend_next_step
    - stage_erp_draft_update
    - escalate

turn_input_defaults:
  risk_class: operational
  contains_high_risk_terms: false
  explicit_approval_language: false

ui_overrides:
  subtitle: "Auto Repair MVP"
```

## 4. Required file layout

Modules should follow a predictable directory convention so authoring is reviewable and tooling can discover them deterministically.

```text
model-packs/<domain>/modules/<module>/
├── module-config.yaml
├── domain-physics.yaml
├── domain-physics.json
├── README.md                  # optional but recommended
├── tool-adapters/
│   └── *.yaml
├── workflows/
│   └── *.yaml or *.md
├── glossary/
│   └── *.md or *.yaml
└── prompts/                   # optional, if the module needs a custom prompt surface
```

### Path conventions

- Module directories must be nested under `model-packs/<domain>/modules/<module>/`.
- Module names must be lowercase and hyphenated (`auto-repair`, `workflow-intake`, `site-ops`).
- `domain-physics.json` is the runtime artifact; `domain-physics.yaml` is the author-editable source.
- Tool adapters should live under `tool-adapters` and be named by capability or version.
- Module-level metadata and defaults must be authored in the module config file, not embedded in the pack manifest.

## 5. Validation rules

A module is valid when all of the following hold:

1. `module-config.yaml` exists and parses as YAML.
2. `domain_physics_path` resolves to a real physics file within the module or pack tree.
3. The module has a deterministic runtime state seed (`initial_module_state`).
4. `default_task_spec` is present and matches the module's operational mode.
5. `domain_step_params` includes any required local defaults the module uses for workflow gating, risk, or routing.
6. `turn_input_defaults` provides fallback values for missing turn fields.
7. When present, `module_id`, `module_path`, and prompt paths resolve to real repository locations.
8. The module does not declare runtime behavior outside the parent pack boundary.

The framework intentionally treats module metadata as locally authoritative and pack-scope only as a registry shell. The pack declares the domain identity; the module declares the behavior.

## 6. Required versus optional behavior contract

### Required

- local config file
- local physics file
- local initial state
- local task defaults
- local turn defaults
- path and naming consistency

### Optional but expected

- tool adapters
- workflow definitions
- glossary or vocabulary descriptors
- custom prompt or persona assets
- README or authoring notes

### Explicitly prohibited in a module contract

- hardcoded cross-pack routing assumptions
- hidden dependency on another module's private structure
- direct mutation of the root framework boundary
- storing raw session dialogue in a module file as authoritative state

## 7. Compatibility and revision policy

Modules should follow a simple compatibility rule:

- a module's `version` or manifest metadata changes when the behavior contract changes
- a breaking change in task semantics, risk gating, or required fields increments the major version
- minor changes may add optional metadata, glossary entries, or tool adapters without breaking execution
- modules should remain backward-compatible within the same parent pack unless `domain_step_params` or authoritative fields are changed

This keeps extraction and reuse predictable without forcing the entire framework to re-author its contracts for each minor module update.

## 8. Relationship to domain packs

The module contract sits under the domain pack contract:

- the pack defines the domain identity, ownership, and routing surface
- the module defines the runtime state and behavior surface inside that domain
- the framework remains unchanged; only the authored metadata contracts expand

This separation ensures the framework only ever sees consistent boundaries rather than ad hoc vertical-specific conventions.

## 9. Migration guidance

The existing repo already demonstrates the expected pattern:

- `model-packs/business-ops/modules/auto-repair/module-config.yaml`
- `model-packs/template/modules/example-module/module-config.yaml`
- `model-packs/coding-agent/modules/core/module-config.yaml`

When authoring a new module, the recommended migration path is:

1. Copy the module layout from `model-packs/template/modules/example-module/`
2. Replace the module directory name and config metadata
3. Write the local `domain-physics.yaml` and generate the JSON runtime artifact
4. Ensure `domain_physics_path` matches the new module path
5. Keep `initial_module_state`, `default_task_spec`, and `turn_input_defaults` deterministic
6. Validate only after the pack-level contract is already satisfied

## 10. Related references

- `docs/7-concepts/domain-pack-authoring-contract-v1.md` — pack-level manifest contract
- `docs/7-concepts/domain-pack-anatomy.md` — domain pack structure and module responsibilities
- `model-packs/template/README.md` — canonical starter layout for a new module and pack
- `model-packs/business-ops/modules/auto-repair/module-config.yaml` — working example of a module config file
