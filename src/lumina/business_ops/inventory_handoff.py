"""Reviewed inventory stock-document handoff intent, without live submission."""

from __future__ import annotations

from typing import Any, Literal


OperationKind = Literal["receiving", "count"]


def build_inventory_handoff(
    *,
    operation_kind: OperationKind,
    draft_record_id: str,
    approval_status: Literal["approved"],
    idempotency_key: str,
) -> dict[str, Any]:
    """Return a canonical pending-submission envelope for a reviewed draft."""
    if operation_kind not in {"receiving", "count"}:
        raise ValueError("operation_kind must be receiving or count")
    if not isinstance(draft_record_id, str) or not draft_record_id.strip():
        raise ValueError("draft_record_id must be a non-empty string")
    if approval_status != "approved":
        raise ValueError("approval_status must be approved")
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise ValueError("idempotency_key must be a non-empty string")

    return {
        "status": "accepted",
        "handoff_status": "pending_submission",
        "operation_kind": operation_kind,
        "draft_record_id": draft_record_id.strip(),
        "idempotency_key": idempotency_key.strip(),
        "live_submit_requested": False,
    }
