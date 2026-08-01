# Odoo Connector (Slice 34 Scaffold)

This package contains a deterministic fixture-only Odoo connector scaffold used for Slice 34 conformance validation.

Scope in this initial scaffold:
- Canonical capability/action declarations via connector manifest
- Canonical request-to-provider payload mapping helpers
- Deterministic fixture execution seam with tenant scope checks
- Canonical provider error normalization

Out of scope in this scaffold:
- Live Odoo transport integration
- Credential exchange / rotation lifecycle
- Full provider feature parity
