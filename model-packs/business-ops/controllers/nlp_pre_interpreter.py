from __future__ import annotations

import re
from typing import Any


_HIGH_RISK_PATTERN = re.compile(r"\b(safety|injury|liability|legal|refund)\b", re.IGNORECASE)
_APPROVAL_PATTERN = re.compile(r"\b(approve|authorized|go ahead|confirmed)\b", re.IGNORECASE)


def pre_interpret(input_text: str, task_context: dict[str, Any]) -> dict[str, Any]:
    text = input_text or ""
    return {
        "contains_high_risk_terms": bool(_HIGH_RISK_PATTERN.search(text)),
        "explicit_approval_language": bool(_APPROVAL_PATTERN.search(text)),
    }
