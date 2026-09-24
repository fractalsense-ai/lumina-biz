---
title: "Slice 67 - Site Profile and Capability Declaration Contract v1"
slice: 67
status: planned
version: 0.1.0
last_updated: 2026-09-24
---

## Purpose

Define a declarative site-profile contract that captures organization/site
identity, capability variance, and override precedence so one shared runtime can
serve materially different locations without site-specific code.

## Scope

- Define declarative organization and site identity fields, location type, and
  capability metadata.
- Define equipment present/absent, services offered/excluded, lease/vendor
  restrictions, operating constraints, active modules, and local overrides.
- Define inheritance and precedence from framework defaults to domain defaults
  to site profile to time-bounded operational override.
- Define validation, provenance, and review requirements for site-profile
  changes.
- Define the explicit rule that site variance must not require site-specific
  runtime code.

### Upstream Dependencies

- Slice 52 domain pack authoring contract.
- Slice 53 module authoring contract.
- Slice 39 generic core/profile direction lock.

## Out of Scope

- Implementing site-profile loaders or runtime mutation paths.
- Hardcoding store-specific branching into workflows or task logic.
- Customer-specific data entry for individual production sites.

## Required Changes

- Document the `site_profile_v1` manifest shape and required/optional fields.
- Document inheritance, override-precedence, and time-bounded override
  semantics.
- Document validation and provenance expectations for capability declarations,
  exclusions, and restrictions.
- Document the no-site-specific-runtime-code rule and how deviations must be
  rejected during review.

## New/Changed Contracts

- New: `site_profile_contract_v1`.
- New: `site_capability_declaration_contract_v1`.
- New: `site_override_precedence_contract_v1`.
- New: `site_profile_provenance_and_validation_policy_v1`.

## Files Likely Touched

- `docs/roadmap/slices/67-site-profile-and-capability-declaration-contract-v1.md`
- `docs/7-concepts/framework-boundary.md`
- `model-packs/README.md`
- `model-packs/business-ops/`

## Acceptance Criteria

- Site-profile fields for identity, location type, capabilities, exclusions,
  restrictions, active modules, and overrides are explicit and versioned.
- Precedence is explicit: framework defaults -> domain defaults -> site profile
  -> time-bounded override.
- Validation and provenance requirements are explicit for every site-specific
  change.
- The contract explicitly states that site variance is declarative and never
  implemented through per-location runtime code.

## Tests

- Documentation review against existing pack/module structure and profile-layer
  direction from Slice 39.
- Link verification for referenced framework-boundary and model-pack files.
- Integrity checks:
  - `python -m lumina.systools.verify_repo`
  - `python -m lumina.systools.manifest_integrity check`

## Ledger/Governance Impact

- Makes site variance auditable instead of hiding location differences in code.
- Reduces long-term fork pressure by turning location-specific behavior into
  governed configuration.

## Follow-Up Slices

- Slice 68.
- Slice 69.
- Slice 71.
- Slice 72.
