---
version: 1.0.0
last_updated: 2026-08-05
---

# Single-Box Operator Runbooks

This document defines top-priority failure and recovery runbooks for single-box pilot operations.

## Runbook A: Route Failure During Command or Workflow Dispatch

### Signals
- API returns 5xx for command or domain command routes.
- Route-specific logs show handler resolution failure or missing contract registration.

### Immediate Actions
1. Freeze non-essential mutation operations.
2. Run smoke check:

```bash
python scripts/single_box_health_check.py --runtime-config model-packs/business-ops/cfg/runtime-config.yaml
```

3. Validate command/schema registration state using normal admin tooling.

### Recovery Steps
1. Re-apply latest validated runtime configuration.
2. Restart API process.
3. Re-run smoke check and readiness check.
4. Execute one deterministic fixture workflow before reopening mutation paths.

### Evidence to Capture
- Health report JSON
- Readiness report JSON
- Relevant route error logs and timestamps

## Runbook B: Connector Degradation

### Signals
- Health report returns `degraded` or `unhealthy` due to connector status.
- Connector preflight or fixture execution reports provider errors/rate limiting.

### Immediate Actions
1. Route affected operations to safe fallback behavior (read-only or escalation only).
2. Notify owner/manager with connector status and impact scope.

### Recovery Steps
1. Validate connector credentials and endpoint connectivity.
2. Re-run deterministic connector fixture checks.
3. Re-run smoke check and verify `healthy` before restoring full operation paths.

### Evidence to Capture
- Connector health statuses from smoke report
- Fixture run outputs
- Timestamped operator decision notes

## Runbook C: Escalation Backlog Growth

### Signals
- Escalation queue grows beyond expected review SLA.
- Repeated pending escalations for identical trigger class.

### Immediate Actions
1. Prioritize by risk class and SLA.
2. Assign explicit reviewers/owners for aging escalations.
3. Restrict non-essential mutation requests until backlog drops.

### Recovery Steps
1. Resolve highest-risk backlog entries first.
2. Confirm escalation resolution path writes expected audit records.
3. Run readiness check to confirm runbook/documentation and backup posture remain valid.

### Evidence to Capture
- Backlog counts over time
- Resolution timestamps
- Any temporary governance control changes

## Post-Incident Checklist

1. Run:

```bash
python scripts/single_box_readiness_check.py
```

2. Confirm readiness report status is `pass`.
3. Archive incident evidence with the next backup cycle.
