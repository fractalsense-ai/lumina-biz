---
version: 1.0.0
last_updated: 2026-08-05
---

# ERP RBAC Mapping V1

**Version:** 1.0.0  
**Status:** Active  
**Last updated:** 2026-08-05

---

## Purpose

Define the canonical mapping from ERP-issued non-system identity claims into Lumina authorization context.

This contract is normative for role/context translation logic and denial behavior. Runtime enforcement implementation is deferred to Slice 38.

---

## Inputs

This mapping consumes claims defined in [erp-jwt-claim-contract-v1](erp-jwt-claim-contract-v1.md):

1. `role`
2. `organization_id`
3. `site_id`
4. Optional `domain_roles`
5. Optional `governed_modules`

---

## Canonical Role Mapping

| ERP claim role | Lumina framework tier | Baseline authorization posture |
|----------------|------------------------|--------------------------------|
| `manager` | `admin` | Domain-scoped governance operations under policy bounds |
| `operator` | `operator` | Operational execution and escalation within scope |
| `reviewer` | `half_operator` | Read and audit focused workflow participation |
| `participant` | `user` | Standard session participation within allowed scope |
| `guest` | `guest` | Minimal, bounded access posture |

Unknown or unmapped `role` values MUST be denied.

---

## Context Binding Rules

1. `organization_id` binds the actor to organization scope.
2. `site_id` binds the actor to site scope within organization.
3. Requests whose effective context does not match token context MUST be denied.
4. Cross-organization access attempts MUST be denied.

### Canonical Context Denial Reasons

| Condition | Denial reason |
|-----------|---------------|
| Unknown role mapping | `INVALID_ROLE_VALUE` |
| Organization mismatch | `ORGANIZATION_MISMATCH` |
| Site mismatch | `SITE_MISMATCH` |

---

## Optional Claim Handling

1. `domain_roles` may enrich module-scoped authorization context.
2. `governed_modules` may further constrain module reach for elevated roles.
3. Optional claims MUST NOT bypass required role/org/site validation.

---

## Scenario Matrix (Documentation-Level)

| Scenario | Expected result |
|----------|-----------------|
| `role=manager`, valid org/site | Map to `admin` posture in bounded scope |
| `role=operator`, valid org/site | Map to `operator` posture |
| Unmapped role value | Deny (`INVALID_ROLE_VALUE`) |
| Token org does not match request org | Deny (`ORGANIZATION_MISMATCH`) |
| Token site does not match request site | Deny (`SITE_MISMATCH`) |

---

## Out of Scope

This contract does not define:

1. Middleware implementation mechanics.
2. Endpoint-specific policy wiring.
3. Token signature verification internals.

These are implemented in Slice 38 using this mapping contract.

---

## Related Contracts

1. [erp-identity-authority-v1](erp-identity-authority-v1.md)
2. [erp-jwt-claim-contract-v1](erp-jwt-claim-contract-v1.md)
3. [rbac-spec](rbac-spec.md)
