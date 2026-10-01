---
version: 1.0.0
last_updated: 2026-08-05
---

# Auth Endpoint Transition Policy V1

**Version:** 1.0.0  
**Status:** Active  
**Last updated:** 2026-08-05

---

## Purpose

Define the Slice 38 transition policy for domain and user authentication endpoint behavior during ERP JWT cutover.

---

## Transition Principle

1. Non-system actor authentication transitions to ERP-issued JWT verification.
2. Legacy non-system profile coexistence is not part of the first vertical path.
3. System admin continuity remains on Lumina system-track auth.

---

## Phase Policy

### Phase 1: Gateway Introduction

1. ERP verification primitives and contracts are introduced.
2. Domain and user middleware migration logic is prepared.

### Phase 2: Hard Cutover

1. Domain and user routes require ERP-issued tokens.
2. Legacy Lumina non-system tokens are denied for domain or user authorization paths.

### Phase 3: Endpoint Cleanup

1. Legacy issuance behaviors for non-system actors are removed or explicitly deprecated.
2. System admin control-plane endpoints remain active and isolated.

---

## Rollback Criteria

Rollback is permitted only when one of the conditions below is true:

1. ERP issuer or audience trust material is invalid or unavailable.
2. Verification-path denial rate exceeds operational threshold.
3. Security incident requires temporary containment.

Rollback actions MUST:

1. Preserve system-track isolation.
2. Emit auditable governance evidence with explicit rollback reason and closure event.
3. Avoid reintroducing unmanaged legacy profile coexistence.

---

## Related Contracts

1. [erp-jwt-verification-gateway-v1](erp-jwt-verification-gateway-v1.md)
2. [erp-jwt-claim-contract-v1](erp-jwt-claim-contract-v1.md)
3. [erp-identity-authority-v1](erp-identity-authority-v1.md)
