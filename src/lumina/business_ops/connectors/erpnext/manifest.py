"""Provider manifest helpers for the ERPNext reference connector."""

from __future__ import annotations


SUPPORTED_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "service/work-order": ("query", "create_draft", "update_draft", "request_commit"),
    "inventory": ("query",),
}


def build_connector_manifest() -> dict[str, object]:
    """Return a canonical connector-manifest payload for ERPNext."""
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
        "connector_id": "connector.erpnext.v1",
        "display_name": "ERPNext Connector",
        "provider_family": "erpnext",
        "version": "1.0.0",
        "capabilities": capabilities,
        "supports_action_classes": sorted(supports_action_classes),
        "authentication": {
            "mode": "runtime_secret",
            "secret_ref": "LUMINA_CONNECTOR_ERP_SECRET",
        },
    }
