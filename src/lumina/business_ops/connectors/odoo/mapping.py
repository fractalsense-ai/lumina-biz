"""Canonical operation to Odoo payload mapping helpers."""

from __future__ import annotations


def _as_dict(payload: object, *, field_name: str) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ValueError(f"{field_name} must be an object")
    return payload


def _as_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"payload.{key} must be a non-empty string")
    return value.strip()


def _as_optional_dict(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"payload.{key} must be an object")
    return dict(value)


def _as_query_envelope(payload: object) -> dict[str, object]:
    data = _as_dict(payload, field_name="payload")
    allowed = {"filters", "fields", "limit", "order_by"}
    extra = sorted(set(data.keys()) - allowed)
    if extra:
        raise ValueError(
            "payload for query must only include filters/fields/limit/order_by; "
            f"unexpected keys: {extra}"
        )
    filters = _as_optional_dict(data, "filters")
    result: dict[str, object] = {"filters": filters}
    fields = data.get("fields")
    if fields is not None:
        if not isinstance(fields, list) or not all(isinstance(item, str) and item.strip() for item in fields):
            raise ValueError("payload.fields must be a list of non-empty strings")
        result["fields"] = [item.strip() for item in fields]
    limit = data.get("limit")
    if limit is not None:
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("payload.limit must be a positive integer")
        result["limit"] = limit
    order_by = data.get("order_by")
    if order_by is not None:
        if not isinstance(order_by, str) or not order_by.strip():
            raise ValueError("payload.order_by must be a non-empty string")
        result["order_by"] = order_by.strip()
    return result


def _as_create_draft_envelope(payload: object) -> dict[str, object]:
    data = _as_dict(payload, field_name="payload")
    allowed = {"record"}
    extra = sorted(set(data.keys()) - allowed)
    if extra:
        raise ValueError(f"payload for create_draft supports only record; unexpected keys: {extra}")
    record = _as_optional_dict(data, "record")
    if not record:
        raise ValueError("payload.record must be a non-empty object for create_draft")
    return {"record": record}


def _as_update_draft_envelope(payload: object) -> dict[str, object]:
    data = _as_dict(payload, field_name="payload")
    allowed = {"record_id", "record"}
    extra = sorted(set(data.keys()) - allowed)
    if extra:
        raise ValueError(f"payload for update_draft supports only record_id/record; unexpected keys: {extra}")
    record_id = _as_str(data, "record_id")
    record = _as_optional_dict(data, "record")
    if not record:
        raise ValueError("payload.record must be a non-empty object for update_draft")
    return {"record_id": record_id, "record": record}


def _as_commit_envelope(payload: object) -> dict[str, object]:
    data = _as_dict(payload, field_name="payload")
    allowed = {"record_id"}
    extra = sorted(set(data.keys()) - allowed)
    if extra:
        raise ValueError(f"payload for request_commit supports only record_id; unexpected keys: {extra}")
    record_id = _as_str(data, "record_id")
    return {"record_id": record_id}


def _unsupported(action_class: str, capability_namespace: str) -> ValueError:
    return ValueError(
        f"Unsupported Odoo mapping for action={action_class!r}, capability={capability_namespace!r}"
    )


def map_operation_to_odoo(request: dict[str, object]) -> dict[str, object]:
    """Map a canonical operation request into an Odoo provider payload."""
    action_class = str(request.get("action_class") or "").strip()
    capability_namespace = str(request.get("capability_namespace") or "").strip()
    payload = request.get("payload")

    if capability_namespace == "service/work-order":
        if action_class == "query":
            query = _as_query_envelope(payload)
            return {
                "model": "helpdesk.ticket",
                "operation": "search_read",
                "domain": query.get("filters", {}),
                **({"fields": query["fields"]} if "fields" in query else {}),
                **({"limit": query["limit"]} if "limit" in query else {}),
                **({"order": query["order_by"]} if "order_by" in query else {}),
            }
        if action_class == "create_draft":
            create = _as_create_draft_envelope(payload)
            return {
                "model": "helpdesk.ticket",
                "operation": "create",
                "values": create["record"],
                "confirm": False,
            }
        if action_class == "update_draft":
            update = _as_update_draft_envelope(payload)
            return {
                "model": "helpdesk.ticket",
                "operation": "write",
                "id": update["record_id"],
                "values": update["record"],
            }
        if action_class == "request_commit":
            commit = _as_commit_envelope(payload)
            return {
                "model": "helpdesk.ticket",
                "operation": "action_confirm",
                "id": commit["record_id"],
            }

    if capability_namespace == "inventory" and action_class == "query":
        query = _as_query_envelope(payload)
        return {
            "model": "product.product",
            "operation": "search_read",
            "domain": query.get("filters", {}),
            **({"fields": query["fields"]} if "fields" in query else {}),
            **({"limit": query["limit"]} if "limit" in query else {}),
            **({"order": query["order_by"]} if "order_by" in query else {}),
        }

    if capability_namespace == "warehouse/storage" and action_class == "query":
        query = _as_query_envelope(payload)
        return {
            "model": "stock.warehouse",
            "operation": "search_read",
            "domain": query.get("filters", {}),
            **({"fields": query["fields"]} if "fields" in query else {}),
            **({"limit": query["limit"]} if "limit" in query else {}),
            **({"order": query["order_by"]} if "order_by" in query else {}),
        }

    if capability_namespace == "logistics/dispatch" and action_class == "query":
        query = _as_query_envelope(payload)
        return {
            "model": "stock.picking",
            "operation": "search_read",
            "domain": query.get("filters", {}),
            **({"fields": query["fields"]} if "fields" in query else {}),
            **({"limit": query["limit"]} if "limit" in query else {}),
            **({"order": query["order_by"]} if "order_by" in query else {}),
        }

    if capability_namespace == "scheduling" and action_class == "query":
        query = _as_query_envelope(payload)
        return {
            "model": "project.task",
            "operation": "search_read",
            "domain": query.get("filters", {}),
            **({"fields": query["fields"]} if "fields" in query else {}),
            **({"limit": query["limit"]} if "limit" in query else {}),
            **({"order": query["order_by"]} if "order_by" in query else {}),
        }

    raise _unsupported(action_class, capability_namespace)
