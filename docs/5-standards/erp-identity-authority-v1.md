---
version: 1.1.0
last_updated: 2026-08-05
---

# ERP Identity Authority V1

**Version:** 1.1.0  
**Status:** Active  
**Last updated:** 2026-08-05

---

## Purpose

Define the authority boundary for identity and authorization context between ERP and Lumina.

This standard establishes ERP as the single source of truth for non-system actors while preserving a separate Lumina-owned system track for framework-level administration.

---

## Scope

This contract applies to:

1. Domain and user identity lifecycle ownership.
2. Organization and site membership authority.
3. Role and context claims that Lumina consumes for non-system actors.
4. Boundary constraints between ERP-issued actor context and Lumina system-track control-plane authority.

---

## Authority Boundary

### ERP Owns (Non-System Identity Authority)

ERP is authoritative for non-system actor identity and membership context, including:

1. User and domain actor identity issuance and lifecycle.
2. Role assignment for non-system actors.
3. Organization and site membership context.
4. Revocation and membership change events that affect non-system access.

### Lumina Owns (System Control-Plane Authority)

Lumina remains authoritative for system-level administration, including:

1. System-track authentication for `root` and `super_admin`.
2. Framework-level control-plane operations.
3. Runtime policy enforcement of accepted identity claims.

### Non-Override Rules

1. ERP cannot directly grant system-track (`root`, `super_admin`) authority.
2. Lumina cannot treat non-system identities as authoritative without ERP-aligned context.
3. No cross-track elevation path may bypass the system-track boundary.

---

## Contract Statements

1. ERP is the SSOT for non-system identity context consumed by Lumina.
2. Lumina system-track credentials remain separate from ERP-issued context.
3. Lumina is the policy-enforcement runtime and does not become the source of truth for ERP-governed identity records.
4. For this first vertical rollout, there is no legacy profile coexistence path for non-system identity.

---

## Out of Scope

This standard does not define:

1. JWT verification middleware implementation details.
2. Detailed claim-level validation logic.
3. Operational key-rotation procedures.

Those are addressed by subsequent Slice 37 contracts and Slice 38 runtime implementation.

---

## Relationship to Other Standards

1. [parallel-authority-tracks](../7-concepts/parallel-authority-tracks.md) provides architectural rationale.
2. [air-gapped-admin-architecture](../8-admin/air-gapped-admin-architecture.md) defines control-plane isolation posture.
3. [auth(3)](../3-functions/auth.md) defines runtime authentication interfaces.
4. [rbac-spec-v1](rbac-spec.md) defines authorization model behavior.
