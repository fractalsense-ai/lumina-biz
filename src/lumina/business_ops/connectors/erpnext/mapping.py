"""Canonical operation to ERPNext payload mapping helpers."""

from __future__ import annotations


def _unsupported(action_class: str, capability_namespace: str) -> ValueError:
    return ValueError(
        f"Unsupported ERPNext mapping for action={action_class!r}, capability={capability_namespace!r}"
    )


def map_operation_to_erpnext(request: dict[str, object]) -> dict[str, object]:
    """Map a canonical operation request into an ERPNext provider payload."""
    action_class = str(request.get("action_class") or "").strip()
    capability_namespace = str(request.get("capability_namespace") or "").strip()
    payload = request.get("payload") if isinstance(request.get("payload"), dict) else {}

    if capability_namespace == "service/work-order":
        if action_class == "query":
            return {
                "doctype": "Work Order",
                "operation": "get_list",
                "filters": dict(payload),
            }
        if action_class == "create_draft":
            return {
                "doctype": "Work Order",
                "operation": "insert",
                "data": dict(payload),
                "submit": False,
            }
        if action_class == "update_draft":
            return {
                "doctype": "Work Order",
                "operation": "update",
                "data": dict(payload),
            }
        if action_class == "request_commit":
            return {
                "doctype": "Work Order",
                "operation": "submit",
                "data": dict(payload),
            }

    if capability_namespace == "inventory" and action_class == "query":
        return {
            "doctype": "Item",
            "operation": "get_list",
            "filters": dict(payload),
        }

    raise _unsupported(action_class, capability_namespace)
