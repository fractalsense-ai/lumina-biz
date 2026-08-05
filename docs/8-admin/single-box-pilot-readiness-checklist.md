---
version: 1.0.0
last_updated: 2026-08-05
---

# Single-Box Pilot Readiness Checklist

Use this checklist before a pilot go/no-go decision.

## Automated Checklist Command

```bash
python scripts/single_box_readiness_check.py \
  --health-report data/staging/single-box-health-report.json \
  --backups-dir data/staging/backups \
  --json-out data/staging/single-box-readiness-report.json
```

PowerShell helper:

```powershell
./scripts/run-single-box-readiness.ps1
```

## Mandatory Gates

1. Health report file exists and is current for this deployment window.
2. Health status is `healthy` (degraded is not pilot-ready).
3. At least one backup archive exists in the configured backup directory.
4. Required single-box runbooks are present:
   - deployment profile
   - backup/restore retention
   - operator runbooks

## Manual Operator Confirmation

1. Route failure runbook reviewed by on-call operator.
2. Connector degradation runbook reviewed by owner/manager.
3. Escalation backlog handling runbook reviewed by governance operator.
4. Last backup and restore drill date recorded.

## Approval Record

- Evaluation timestamp:
- Readiness report path:
- Evaluator:
- Result (`pass` / `fail`):
- Follow-up actions (if fail):
