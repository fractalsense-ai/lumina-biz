---
version: 1.0.0
last_updated: 2026-08-05
---

# Single-Box Deployment Profile and Health Checks

This guide defines the Slice 36 single-box operational profile for local-first pilot sites.

## Profile Contract

The single-box profile assumes one host runs:
1. Lumina API runtime
2. Domain-pack runtime assets (physics, prompts, profiles)
3. Local institutional-memory artifacts
4. Optional external connector endpoints (for example ERP adapters)

The deployment remains valid without mandatory external network dependencies, except optional business-system connectors.

## Startup Ordering

Recommended startup order:
1. Activate runtime environment and set required env vars.
2. Seed system-physics commitment evidence.
3. Start Lumina API server.
4. Run single-box smoke check and inspect JSON health report.
5. Run pre-integration scenarios only after smoke status is healthy.

## Deterministic Health Report

Run:

```bash
python scripts/single_box_health_check.py \
  --runtime-config model-packs/business-ops/cfg/runtime-config.yaml \
  --json-out data/staging/single-box-health-report.json
```

PowerShell helper:

```powershell
./scripts/run-single-box-smoke.ps1
```

Bash helper:

```bash
bash scripts/run-single-box-smoke.sh
```

### Status Semantics

- `healthy`: all required runtime paths exist; optional memory directories exist; connector statuses are healthy.
- `degraded`: no unhealthy checks, but at least one degraded signal (for example connector health degraded or missing optional memory directory).
- `unhealthy`: at least one required runtime asset missing or connector status unhealthy.

## Connector Degraded-Mode Validation

You can pass a connector registry payload to validate degraded-mode deterministically:

```bash
python scripts/single_box_health_check.py \
  --runtime-config model-packs/business-ops/cfg/runtime-config.yaml \
  --connector-registry data/staging/connector-registry-example.json
```

Payload format accepts either:
1. A top-level list of connector entries.
2. An object containing `connector_registry_entries`.

Each entry should include:
- `connector_instance_id`
- `organization_id`
- `site_id`
- `health_status` (`healthy`, `degraded`, `unhealthy`)

## Smoke Gate Behavior

Use `--fail-on-degraded` when CI or pilot readiness requires strictly healthy status.

- default exit policy: fail only for unhealthy
- strict policy: fail for degraded and unhealthy

## Pilot-Site Notes

- Keep `data/staging/single-box-health-report.json` as deployment evidence.
- Treat repeated degraded status as an operator action item before production mutation paths are enabled.
- This profile hardens operations only and does not change canonical workflow semantics.
