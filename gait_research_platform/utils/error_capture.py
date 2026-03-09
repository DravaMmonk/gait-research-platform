from __future__ import annotations

import os
import traceback
from typing import Any


def format_exception_payload(exc: Exception, stage: str) -> dict[str, Any]:
    include_traceback = os.getenv("DEBUG_AGENT", "").lower() in {"1", "true", "yes", "on"}
    payload: dict[str, Any] = {
        "type": exc.__class__.__name__,
        "message": str(exc),
        "stage": stage,
        "traceback": traceback.format_exc() if include_traceback else None,
    }
    if include_traceback:
        payload["debug"] = {
            "exception_repr": repr(exc),
        }
    return payload
