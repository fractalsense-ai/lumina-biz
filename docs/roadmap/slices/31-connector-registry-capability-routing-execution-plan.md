---
title: "Slice 31 Execution Plan - Connector Registry and Capability Routing"
slice: 31
status: planned
version: 0.1.0
last_updated: 2026-07-26
source_overview: docs/roadmap/slices/31-business-ops-pack-bootstrap.md
---

## Objective

Execute Slice 31 by adding deterministic connector registry and capability
routing contracts so Business Ops can resolve connector targets predictably per
organization/site scope without granting execution authority.

## Exit Criteria (Slice Completion)

- Connector registry, capability policy, and connector resolution contracts
  exist under standards and validate deterministically.
- Routing precedence is implemented exactly and covered by deterministic tests.
- Single-primary and multi-connector scenarios both pass with fixed fixtures.
- Missing-route, ambiguous-route, unsupported-capability, and unhealthy-target
  outcomes return structured errors.
- No credential material appears in registry, routing policy, or resolution
  artifacts.

## Work Plan

### Phase 1 - Contract Freeze

1. Define and review three canonical contracts:
   - connector_registry_entry
   - capability_route_policy
   - connector_resolution_result
2. Define idempotency and correlation requirements for mutation operation
   routing requests.
3. Freeze naming/versioning for the first implementation pass.

Deliverables:
- New schema files under standards.
- Contract matrix mapping schema, owner, and test coverage.

### Phase 2 - Deterministic Resolution Engine

1. Implement pure connector resolution with fixed precedence:
   - operation-level override
   - capability route
   - site primary connector
   - organization default connector
   - no-route failure
2. Ensure identical inputs always produce identical outputs.
3. Keep engine side-effect free (no provider calls and no mutations).

Deliverables:
- Pure routing module and fixtures with deterministic expected outcomes.

### Phase 3 - Capability and Health Gating

1. Validate capability compatibility before selecting a connector.
2. Enforce connector health status checks before returning selected route.
3. Return explicit structured failure reasons for unsupported capability,
   unhealthy connector, and ambiguity.

Deliverables:
- Validation helpers and structured error payloads.
- Negative tests for all gate failures.

### Phase 4 - API and Ledger Wiring

1. Add scoped API preflight for connector resolution requests.
2. Emit transcript-free auditable routing decision metadata.
3. Preserve governance boundaries: routing resolves target only and never
   authorizes execute/commit.

Deliverables:
- API route(s), model updates, and decision evidence wiring.

### Phase 5 - Regression and Governance Gate

1. Run contract, service, API, and regression test suites.
2. Verify manifest integrity and deterministic outputs in CI/local.
3. Validate no credential-bearing fields are accepted in routing artifacts.

Deliverables:
- Green validation evidence and updated roadmap status artifacts.

## Proposed File Targets

- standards/connector-registry-entry-schema-v1.json
- standards/capability-route-policy-schema-v1.json
- standards/connector-resolution-result-schema-v1.json
- src/lumina/business_ops/routing.py
- src/lumina/api/routes/connector_routing.py
- src/lumina/api/models.py
- tests/test_connector_routing.py
- tests/test_connector_routing_contracts.py
- docs/7-concepts/business-system-capability-taxonomy.md
- docs/roadmap/slices/31-business-ops-pack-bootstrap.md

## Risk Register

1. Ambiguous route precedence causing nondeterministic connector selection.
   - Mitigation: enforce strict precedence and deterministic tie-break rules.
2. Capability drift between registry and policies.
   - Mitigation: schema constraints plus conformance tests for each namespace.
3. Health-state staleness leading to brittle routing.
   - Mitigation: explicit health timestamp and stale-health failure path.
4. Credential leakage through free-form metadata fields.
   - Mitigation: recursive denylist-safe object enforcement in all new
     contracts.

## Implementation-Ready PR Description Template

### Title

Slice 31: Connector registry and deterministic capability routing

### Scope

- Add provider-neutral contracts for connector registry, capability routing
  policy, and connector resolution results.
- Implement deterministic connector resolution precedence with capability/health
  gating.
- Add scoped preflight API and auditable routing-decision evidence.

### Acceptance Criteria

- Connector resolution is deterministic and precedence-compliant.
- Single-primary and multi-connector resolution paths are both supported.
- Missing-route, ambiguity, unsupported capability, and unhealthy target return
  structured errors.
- Routing does not grant execution authority and emits no credential material.

### Test Checklist

- [ ] Contract validation tests for all Slice 31 schemas.
- [ ] Deterministic precedence tests for override, capability, site, org,
      and no-route paths.
- [ ] Negative tests for ambiguous routes and missing idempotency key.
- [ ] Capability and health-gate tests including unhealthy and stale-health
      paths.
- [ ] API auth/scope tests for cross-organization and cross-site denial.
- [ ] Manifest integrity and full regression suites remain green.

### Out of Scope Confirmations

- No provider-specific client implementation.
- No business-operation execution or commit authority changes.
- No distributed transaction orchestration.

## Suggested Execution Order

1. Land and validate Slice 31 standards contracts.
2. Implement pure deterministic routing engine.
3. Add capability/health gating and structured failure mapping.
4. Add scoped API preflight and routing decision evidence.
5. Run full validation matrix and update roadmap status when complete.
