"""Canonical operation to ERPNext payload mapping helpers."""

from __future__ import annotations

import math


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


def _as_query_envelope(payload: object, *, allow_query_type: bool = False) -> dict[str, object]:
    data = _as_dict(payload, field_name="payload")
    allowed = {"filters", "fields", "limit", "order_by"}
    if allow_query_type:
        allowed.add("query_type")
    extra = sorted(set(data.keys()) - allowed)
    if extra:
        raise ValueError(
            "payload for query must only include filters/fields/limit/order_by; "
            f"unexpected keys: {extra}"
        )
    filters = _as_optional_dict(data, "filters")
    result: dict[str, object] = {"filters": filters}
    if "query_type" in data:
        query_type = data["query_type"]
        if not isinstance(query_type, str) or query_type not in {"items", "stock_balances"}:
            raise ValueError("payload.query_type must be items or stock_balances")
        result["query_type"] = query_type
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


def _validate_draft_docstatus(record: dict[str, object], action_class: str) -> None:
    if "docstatus" not in record:
        return
    docstatus = record["docstatus"]
    is_draft = (
        (isinstance(docstatus, int) and not isinstance(docstatus, bool) and docstatus == 0)
        or (isinstance(docstatus, str) and docstatus.strip() == "0")
    )
    if not is_draft:
        raise ValueError(f"payload.record.docstatus must be 0 for inventory {action_class}")


def _map_inventory_record(record: dict[str, object], operation_kind: str) -> dict[str, object]:
    if operation_kind == "receiving":
        for field_name in ("stock_entry_type", "purpose"):
            value = record.get(field_name)
            if value is not None and value != "Material Receipt":
                raise ValueError(f"receiving draft {field_name} must be Material Receipt")

        mapped = {key: value for key, value in record.items() if key != "purpose"}
        mapped["stock_entry_type"] = "Material Receipt"
        return mapped

    mapped = dict(record)
    purpose = mapped.get("purpose")
    if purpose is not None and purpose != "Stock Reconciliation":
        raise ValueError("count draft purpose must be Stock Reconciliation")
    return mapped


def _validate_count_create_record(record: dict[str, object]) -> dict[str, object]:
    mapped = _map_inventory_record(record, "count")
    _as_str(mapped, "company")
    items = mapped.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("count draft record.items must be a non-empty list")

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"count draft record.items[{index}] must be an object")
        _as_str(item, "item_code")
        _as_str(item, "warehouse")
        quantity = item.get("qty")
        valuation_rate = item.get("valuation_rate")
        if quantity in (None, "") and valuation_rate in (None, ""):
            raise ValueError(
                f"count draft record.items[{index}] requires qty or valuation_rate"
            )
        for field_name, value in (("qty", quantity), ("valuation_rate", valuation_rate)):
            if value in (None, ""):
                continue
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
                or (isinstance(value, float) and not math.isfinite(value))
            ):
                raise ValueError(
                    f"count draft record.items[{index}].{field_name} must be a finite non-negative number"
                )

    mapped["purpose"] = "Stock Reconciliation"
    return mapped


def _as_create_draft_envelope(payload: object) -> dict[str, object]:
    data = _as_dict(payload, field_name="payload")
    allowed = {"record", "operation_kind"}
    extra = sorted(set(data.keys()) - allowed)
    if extra:
        raise ValueError(f"payload for create_draft supports only record; unexpected keys: {extra}")
    record = _as_optional_dict(data, "record")
    if not record:
        raise ValueError("payload.record must be a non-empty object for create_draft")
    _validate_draft_docstatus(record, "create_draft")
    operation_kind = data.get("operation_kind")
    if operation_kind is not None:
        if not isinstance(operation_kind, str) or operation_kind not in {"receiving", "count"}:
            raise ValueError("payload.operation_kind must be receiving or count")
    return {"record": record, **({"operation_kind": operation_kind} if operation_kind else {})}


def _as_update_draft_envelope(payload: object) -> dict[str, object]:
    data = _as_dict(payload, field_name="payload")
    allowed = {"record_id", "record", "operation_kind"}
    extra = sorted(set(data.keys()) - allowed)
    if extra:
        raise ValueError(f"payload for update_draft supports only record_id/record; unexpected keys: {extra}")
    record_id = _as_str(data, "record_id")
    record = _as_optional_dict(data, "record")
    if not record:
        raise ValueError("payload.record must be a non-empty object for update_draft")
    _validate_draft_docstatus(record, "update_draft")
    operation_kind = data.get("operation_kind")
    if operation_kind is not None:
        if not isinstance(operation_kind, str) or operation_kind not in {"receiving", "count"}:
            raise ValueError("payload.operation_kind must be receiving or count")
    return {"record_id": record_id, "record": record, **({"operation_kind": operation_kind} if operation_kind else {})}


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
        f"Unsupported ERPNext mapping for action={action_class!r}, capability={capability_namespace!r}"
    )


def map_operation_to_erpnext(request: dict[str, object]) -> dict[str, object]:
    """Map a canonical operation request into an ERPNext provider payload."""
    action_class = str(request.get("action_class") or "").strip()
    capability_namespace = str(request.get("capability_namespace") or "").strip()
    payload = request.get("payload")

    if capability_namespace == "service/work-order":
        if action_class == "query":
            query = _as_query_envelope(payload)
            return {
                "doctype": "Work Order",
                "operation": "get_list",
                "filters": query.get("filters", {}),
                **({"fields": query["fields"]} if "fields" in query else {}),
                **({"limit": query["limit"]} if "limit" in query else {}),
                **({"order_by": query["order_by"]} if "order_by" in query else {}),
            }
        if action_class == "create_draft":
            create = _as_create_draft_envelope(payload)
            return {
                "doctype": "Work Order",
                "operation": "insert",
                "data": create["record"],
                "submit": False,
            }
        if action_class == "update_draft":
            update = _as_update_draft_envelope(payload)
            return {
                "doctype": "Work Order",
                "operation": "update",
                "name": update["record_id"],
                "data": update["record"],
            }
        if action_class == "request_commit":
            commit = _as_commit_envelope(payload)
            return {
                "doctype": "Work Order",
                "operation": "submit",
                "name": commit["record_id"],
            }

    if capability_namespace == "inventory":
        if action_class == "query":
            query = _as_query_envelope(payload, allow_query_type=True)
            query_type = query.get("query_type", "items")
            if query_type == "stock_balances":
                fields = query.get("fields", ["item_code", "warehouse", "actual_qty", "stock_uom"])
                return {
                    "doctype": "Bin",
                    "operation": "get_list",
                    "filters": query.get("filters", {}),
                    "fields": fields,
                    **({"limit": query["limit"]} if "limit" in query else {}),
                    **({"order_by": query["order_by"]} if "order_by" in query else {}),
                }
            return {
                "doctype": "Item",
                "operation": "get_list",
                "filters": query.get("filters", {}),
                **({"fields": query["fields"]} if "fields" in query else {}),
                **({"limit": query["limit"]} if "limit" in query else {}),
                **({"order_by": query["order_by"]} if "order_by" in query else {}),
            }
        if action_class == "create_draft":
            create = _as_create_draft_envelope(payload)
            operation_kind = create.get("operation_kind")
            if operation_kind == "receiving":
                doctype = "Stock Entry"
            elif operation_kind == "count":
                doctype = "Stock Reconciliation"
            else:
                raise ValueError("inventory create_draft requires operation_kind receiving or count")
            record = (
                _validate_count_create_record(create["record"])
                if operation_kind == "count"
                else _map_inventory_record(create["record"], str(operation_kind))
            )
            return {
                "doctype": doctype,
                "operation": "insert",
                "data": record,
                "submit": False,
            }
        if action_class == "update_draft":
            update = _as_update_draft_envelope(payload)
            operation_kind = update.get("operation_kind")
            if operation_kind == "receiving":
                doctype = "Stock Entry"
            elif operation_kind == "count":
                doctype = "Stock Reconciliation"
            else:
                raise ValueError("inventory update_draft requires operation_kind receiving or count")
            record = _map_inventory_record(update["record"], str(operation_kind))
            return {
                "doctype": doctype,
                "operation": "update",
                "name": update["record_id"],
                "data": record,
            }

    if capability_namespace == "sales/pos" and action_class == "query":
        query = _as_query_envelope(payload)
        return {
            "doctype": "POS Invoice",
            "operation": "get_list",
            "filters": query.get("filters", {}),
            **({"fields": query["fields"]} if "fields" in query else {}),
            **({"limit": query["limit"]} if "limit" in query else {}),
            **({"order_by": query["order_by"]} if "order_by" in query else {}),
        }

    if capability_namespace == "warehouse/storage" and action_class == "query":
        query = _as_query_envelope(payload)
        return {
            "doctype": "Warehouse",
            "operation": "get_list",
            "filters": query.get("filters", {}),
            **({"fields": query["fields"]} if "fields" in query else {}),
            **({"limit": query["limit"]} if "limit" in query else {}),
            **({"order_by": query["order_by"]} if "order_by" in query else {}),
        }

    if capability_namespace == "logistics/dispatch" and action_class == "query":
        query = _as_query_envelope(payload)
        return {
            "doctype": "Delivery Note",
            "operation": "get_list",
            "filters": query.get("filters", {}),
            **({"fields": query["fields"]} if "fields" in query else {}),
            **({"limit": query["limit"]} if "limit" in query else {}),
            **({"order_by": query["order_by"]} if "order_by" in query else {}),
        }

    if capability_namespace == "scheduling" and action_class == "query":
        query = _as_query_envelope(payload)
        return {
            "doctype": "Task",
            "operation": "get_list",
            "filters": query.get("filters", {}),
            **({"fields": query["fields"]} if "fields" in query else {}),
            **({"limit": query["limit"]} if "limit" in query else {}),
            **({"order_by": query["order_by"]} if "order_by" in query else {}),
        }

    raise _unsupported(action_class, capability_namespace)
