"""Deterministic inventory discrepancy evidence without stock mutations."""

from __future__ import annotations

import math
from typing import Any


def _finite_number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be a finite number")
    if result < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return result


def calculate_inventory_discrepancy(
    *,
    item_code: str,
    warehouse: str,
    counted_qty: object,
    on_hand_qty: object,
    valuation_rate: object | None = None,
) -> dict[str, Any]:
    """Calculate provider-neutral review evidence for a physical count."""
    if not isinstance(item_code, str) or not item_code.strip():
        raise ValueError("item_code must be a non-empty string")
    if not isinstance(warehouse, str) or not warehouse.strip():
        raise ValueError("warehouse must be a non-empty string")

    counted = _finite_number(counted_qty, "counted_qty")
    on_hand = _finite_number(on_hand_qty, "on_hand_qty")
    variance = counted - on_hand

    evidence: dict[str, Any] = {
        "item_code": item_code.strip(),
        "warehouse": warehouse.strip(),
        "counted_qty": counted,
        "on_hand_qty": on_hand,
        "variance_qty": variance,
        "absolute_variance_qty": abs(variance),
        "review_required": variance != 0,
        "stock_mutation_requested": False,
    }

    if valuation_rate is not None:
        rate = _finite_number(valuation_rate, "valuation_rate")
        evidence["valuation_rate"] = rate
        evidence["estimated_variance_value"] = round(variance * rate, 6)

    return evidence
