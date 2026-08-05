"""Provider manifest helpers for the Odoo reference connector."""

from __future__ import annotations


SUPPORTED_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "service/work-order": ("query", "create_draft", "update_draft", "request_commit"),
    "inventory": ("query",),
    "warehouse/storage": ("query",),
    "logistics/dispatch": ("query",),
    "scheduling": ("query",),
}


def build_connector_manifest() -> dict[str, object]:
    """Return a canonical connector-manifest payload for Odoo."""
    capabilities = [
        {
            "namespace": namespace,
            "supported_actions": list(actions),
        }
        for namespace, actions in sorted(SUPPORTED_CAPABILITIES.items())
    ]

    supports_action_classes: set[str] = set()
    for actions in SUPPORTED_CAPABILITIES.values():
        supports_action_classes.update(actions)

    return {
        "connector_id": "connector.odoo.v1",
        "display_name": "Odoo Connector",
        "provider_family": "odoo",
        "version": "1.0.0",
        "capabilities": capabilities,
        "supports_action_classes": sorted(supports_action_classes),
        "authentication": {
            "mode": "runtime_secret",
            "secret_ref": "LUMINA_CONNECTOR_ODOO_SECRET",
        },
    }
