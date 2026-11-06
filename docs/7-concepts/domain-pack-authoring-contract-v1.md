---
version: 1.0.0
last_updated: 2026-09-22
---

# Domain Pack Authoring Contract v1

**Status:** Active  
**Applies to:** every `model-packs/<domain>/pack.yaml` manifest

This document defines the normative contract for a domain pack manifest. It establishes the minimum required identity, governance, routing, and compatibility metadata that a pack must declare before it is accepted by the framework.

## 1. Contract scope

The framework treats a domain pack as a self-contained unit with explicit identity and a stable routing surface. The manifest is the contract boundary:

- `pack_id` identifies the domain pack in logs, routing, and session provenance
- `version` defines the pack version and compatibility surface
- `description` provides the human-readable summary used by tooling and operators
- `layers` states which files belong to the Model / Controller / View / docs structure
- `modules` declares the available module IDs for this pack
- `default_module` provides the default route when a user or workflow does not specify a module
- `entry_points` links the runtime configuration and adapter entry points into the framework

## 2. Required fields

The following keys are required in every `pack.yaml`:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `pack_id` | string | Yes | Stable pack identifier; matches the directory name when practical |
| `version` | string | Yes | SemVer-style version string; use `0.1.0` for draft packs |
| `description` | string | Yes | One-line or short paragraph describing the domain |
| `layers` | mapping | Yes | Declares component ownership by layer: model, controller, domain_lib, view, docs |
| `modules` | list[string] | Yes | Non-empty list of module IDs the pack provides |
| `default_module` | string | Yes | Must be present in `modules` |
| `entry_points` | mapping | Yes | Must include at least `runtime_config` and the runtime adapter references |

### Required `entry_points` entries

At minimum, the framework expects the following runtime-bound access points:

| Entry point | Required | Meaning |
|---|---:|---|
| `runtime_config` | Yes | Relative path to the runtime config for the pack |
| `runtime_adapter` | Recommended | Relative path to the runtime adapter entrypoint |
| `nlp_pre_interpreter` | Recommended | Relative path to the deterministic NLP gate adapter |
| `ui_config` | Optional | UI config path if the pack exposes a custom UI |

## 3. Optional but recognized fields

The following keys are optional and recognized by downstream tooling or authoring conventions:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `owner` | string | No | Domain authority or owning team identifier |
| `vertical_type` | string | No | Typical values include `framework`, `seed_vertical`, `business_ops`, or `domain` |
| `scope` | string or mapping | No | Governance / deployment scope metadata |
| `routing_defaults` | mapping | No | Default routing hints and module precedence |
| `module_map` | mapping | No | Module-specific overrides for adapters and prompts |
| `metadata` | mapping | No | Arbitrary pack metadata for tooling |
| `maintainers` | list[string] | No | Contact or ownership list |
| `contract_version` | string | No | Explicit compatibility marker. If absent, the pack is treated as legacy `v1` by default |
| `compatibility` | mapping | No | Declares forward/backward compatibility expectations |
| `notes` | string | No | Human guidance for pack migration or release notes |

## 4. Validation rules

The framework validates a manifest with the following rules:

1. `pack.yaml` must parse as a YAML mapping.
2. Required keys must be present and non-empty.
3. `modules` must be a non-empty list of strings.
4. `default_module` must match one of the declared `modules` values.
5. `layers` must be a mapping, and `entry_points` must be a mapping.
6. `entry_points.runtime_config` must resolve to a real file in the pack directory or repository.

The runtime helper `lumina.core.pack_contract.validate_pack_manifest()` enforces these rules for pack authoring and registry lookups.

## 5. Versioning and compatibility policy

The versioning policy is intentionally simple and deterministic:

- `version` must be a non-empty string.
- Use semantic versioning for pack evolution: `0.1.0`, `0.2.0`, `1.0.0`, etc.
- Pack compatibility is defined by the major version number. A newer pack with the same major version should remain compatible unless the `compatibility` block explicitly declares otherwise.
- Breaking changes in pack identity, routing metadata, or default module semantics must increment the major version.
- Non-breaking metadata improvements may be added in a minor or patch revision.

This policy gives authors a stable surface for extraction and future repository portability without forcing a framework change for every metadata addition.

## 6. Migration guidance for existing packs

The current repository packs already conform to the canonical structure:

- `model-packs/system/pack.yaml`
- `model-packs/coding-agent/pack.yaml`
- `model-packs/template/pack.yaml`
- `model-packs/business-ops/pack.yaml`

When creating a new pack, the simplest migration path is:

1. Copy `model-packs/template/pack.yaml`
2. Replace the identity fields with the new domain's values
3. Set `modules` and `default_module` to the actual module IDs
4. Ensure `entry_points` points to the correct config and adapter files
5. Validate with `validate_pack_manifest()` before committing

## 7. Related references

- `model-packs/README.md` — pack taxonomy and framework boundary
- `docs/7-concepts/framework-boundary.md` — the base framework vs seed vertical boundary
- `docs/7-concepts/domain-pack-anatomy.md` — the structural definition of a domain pack
- `src/lumina/core/pack_contract.py` — validation logic for the contract
