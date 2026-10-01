---
version: 1.0.0
last_updated: 2026-08-05
---

# ERP RBAC Mapping Scenarios

Worked examples for claim-to-RBAC mapping behavior defined by:

1. [erp-jwt-claim-contract-v1](../5-standards/erp-jwt-claim-contract-v1.md)
2. [erp-rbac-mapping-v1](../5-standards/erp-rbac-mapping-v1.md)

## Scenario 1: Manager mapping

Input claims:

```json
{
  "role": "manager",
  "organization_id": "org-a",
  "site_id": "site-1"
}
```

Expected:

1. Role maps to Lumina `admin` tier posture.
2. Context binds to `org-a/site-1`.
3. Access remains policy-bounded by module and scope rules.

## Scenario 2: Operator mapping

Input claims:

```json
{
  "role": "operator",
  "organization_id": "org-a",
  "site_id": "site-1"
}
```

Expected:

1. Role maps to Lumina `operator` tier posture.
2. Execution and escalation rights stay within bound organization/site context.

## Scenario 3: Invalid role value

Input claims:

```json
{
  "role": "site_owner_unrecognized",
  "organization_id": "org-a",
  "site_id": "site-1"
}
```

Expected:

1. Deny with `INVALID_ROLE_VALUE`.
2. Record denial event with actor and reason.

## Scenario 4: Organization mismatch

Input claims:

```json
{
  "role": "operator",
  "organization_id": "org-a",
  "site_id": "site-1"
}
```

Request context:

```json
{
  "organization_id": "org-b",
  "site_id": "site-1"
}
```

Expected:

1. Deny with `ORGANIZATION_MISMATCH`.
2. No fallback to broader scope.

## Scenario 5: Site mismatch

Input claims:

```json
{
  "role": "operator",
  "organization_id": "org-a",
  "site_id": "site-1"
}
```

Request context:

```json
{
  "organization_id": "org-a",
  "site_id": "site-2"
}
```

Expected:

1. Deny with `SITE_MISMATCH`.
2. Record denial reason for audit review.
