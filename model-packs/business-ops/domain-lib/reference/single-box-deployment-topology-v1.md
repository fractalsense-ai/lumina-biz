# Single-Box Deployment Topology v1

Assumptions:
- Lumina API and ERP connector adapters run on one local host.
- ERP system access is through a bounded adapter boundary.
- Multi-site access is through VPN with site-scoped auth context.
- Institutional memory indexes are local-first and periodically backed up.

Guardrails:
- No direct production mutation without owner or manager approval.
- All staged draft mutations carry correlation and idempotency metadata.
- Escalations remain system-governed and append-only.
