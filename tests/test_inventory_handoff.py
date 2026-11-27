from __future__ import annotations

import pytest

from lumina.business_ops import build_inventory_handoff


@pytest.mark.unit
@pytest.mark.parametrize(
    ("operation_kind", "draft_record_id"),
    [("receiving", "STE-0001"), ("count", "SR-0001")],
)
def test_build_inventory_handoff_pending_submission(operation_kind: str, draft_record_id: str) -> None:
    handoff = build_inventory_handoff(
        operation_kind=operation_kind,
        draft_record_id=draft_record_id,
        approval_status="approved",
        idempotency_key="idem-1",
    )

    assert handoff == {
        "status": "accepted",
        "handoff_status": "pending_submission",
        "operation_kind": operation_kind,
        "draft_record_id": draft_record_id,
        "idempotency_key": "idem-1",
        "live_submit_requested": False,
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    ("draft_record_id", "approval_status", "idempotency_key", "message"),
    [
        ("   ", "approved", "idem-1", "draft_record_id"),
        ("STE-0001", "pending", "idem-1", "approval_status"),
        ("STE-0001", "approved", "   ", "idempotency_key"),
    ],
)
def test_build_inventory_handoff_rejects_unapproved_or_invalid_input(
    draft_record_id: str,
    approval_status: str,
    idempotency_key: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_inventory_handoff(
            operation_kind="receiving",
            draft_record_id=draft_record_id,
            approval_status=approval_status,
            idempotency_key=idempotency_key,
        )
