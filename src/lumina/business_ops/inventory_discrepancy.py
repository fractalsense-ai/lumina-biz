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
    absolute_variance = abs(variance)
    if not math.isfinite(variance) or not math.isfinite(absolute_variance):
        raise ValueError("variance_qty is outside the finite numeric range")

    evidence: dict[str, Any] = {
        "item_code": item_code.strip(),
        "warehouse": warehouse.strip(),
        "counted_qty": counted,
        "on_hand_qty": on_hand,
        "variance_qty": variance,
        "absolute_variance_qty": absolute_variance,
        "review_required": variance != 0,
        "stock_mutation_requested": False,
    }

    if valuation_rate is not None:
        rate = _finite_number(valuation_rate, "valuation_rate")
        evidence["valuation_rate"] = rate
        estimated_variance_value = variance * rate
        if not math.isfinite(estimated_variance_value):
            raise ValueError("estimated_variance_value is outside the finite numeric range")
        evidence["estimated_variance_value"] = round(estimated_variance_value, 6)

    return evidence
