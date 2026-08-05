---
version: 1.0.0
last_updated: 2026-08-05
---

# ERP Auth Fallback Policy V1

**Version:** 1.0.0  
**Status:** Active  
**Last updated:** 2026-08-05

---

## Purpose

Define bounded break-glass behavior when ERP identity infrastructure is unavailable.

Fallback is a temporary safety posture, not a normal operating mode.

---

## Activation Preconditions

Fallback MAY be activated only when at least one condition is true:

1. ERP issuer endpoint is unavailable.
2. ERP key material endpoint is unavailable or timing out.
3. ERP identity validation service outage blocks non-system actor authentication.

---

## Hard Constraints

1. Fallback MUST be explicitly activated by an authorized operator.
2. Fallback MUST be time-bounded.
3. Fallback MUST be auditable.
4. Fallback MUST be non-default.
5. Fallback MUST NOT grant system-track (`root`, `super_admin`) authority.

---

## Time Bound

1. Default maximum fallback window: 4 hours.
2. Any extension requires explicit re-authorization and a new governance event.
3. Fallback expiration MUST automatically return the system to strict ERP validation posture.

---

## Operational Posture During Fallback

During active fallback, deployments SHOULD constrain non-system operations to reduced-risk modes (for example read-only or escalation-first behavior) until ERP validation is restored.

---

## Required Audit Evidence

Each activation and deactivation MUST write an auditable governance event containing:

1. Operator identifier.
2. Activation timestamp.
3. Planned expiration timestamp.
4. Trigger reason category.
5. Recovery status at deactivation.

---

## Scenario Matrix (Documentation-Level)

| Scenario | Expected result |
|----------|-----------------|
| ERP issuer timeout and operator activates fallback for bounded window | Fallback active, governance event recorded |
| Fallback window expires | Automatic return to strict ERP validation posture |
| Operator requests extension before expiry | New bounded window only with explicit governance event |
| ERP validation restored early | Operator deactivates fallback and records closure event |

---

## Out of Scope

This policy does not define:

1. Concrete command-line tooling for activation/deactivation.
2. Runtime implementation details of fallback mode switching.
3. Middleware internals.

These are implementation concerns for Slice 38 and operational scripting slices.

---

## Related Contracts

1. [erp-identity-authority-v1](erp-identity-authority-v1.md)
2. [erp-jwt-claim-contract-v1](erp-jwt-claim-contract-v1.md)
3. [secrets-and-runtime-config](../8-admin/secrets-and-runtime-config.md)
