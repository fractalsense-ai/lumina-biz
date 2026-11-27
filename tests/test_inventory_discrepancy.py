from __future__ import annotations

import math

import pytest

from lumina.business_ops import calculate_inventory_discrepancy


@pytest.mark.unit
def test_inventory_discrepancy_calculates_positive_variance() -> None:
    evidence = calculate_inventory_discrepancy(
        item_code="ITEM-1",
        warehouse="STORE - T",
        counted_qty=12,
        on_hand_qty=10,
        valuation_rate=2.5,
    )

    assert evidence["variance_qty"] == 2
    assert evidence["absolute_variance_qty"] == 2
    assert evidence["estimated_variance_value"] == 5
    assert evidence["review_required"] is True
    assert evidence["stock_mutation_requested"] is False


@pytest.mark.unit
def test_inventory_discrepancy_calculates_negative_variance() -> None:
    evidence = calculate_inventory_discrepancy(
        item_code="ITEM-1",
        warehouse="STORE - T",
        counted_qty=8,
        on_hand_qty=10,
    )

    assert evidence["variance_qty"] == -2
    assert evidence["absolute_variance_qty"] == 2
    assert evidence["review_required"] is True


@pytest.mark.unit
def test_inventory_discrepancy_no_review_when_counts_match() -> None:
    evidence = calculate_inventory_discrepancy(
        item_code="ITEM-1",
        warehouse="STORE - T",
        counted_qty=10,
        on_hand_qty=10,
    )

    assert evidence["variance_qty"] == 0
    assert evidence["review_required"] is False


@pytest.mark.unit
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_inventory_discrepancy_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ValueError, match="finite number"):
        calculate_inventory_discrepancy(
            item_code="ITEM-1",
            warehouse="STORE - T",
            counted_qty=value,
            on_hand_qty=10,
        )


@pytest.mark.unit
def test_inventory_discrepancy_rejects_negative_quantity() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        calculate_inventory_discrepancy(
            item_code="ITEM-1",
            warehouse="STORE - T",
            counted_qty=-1,
            on_hand_qty=10,
        )
