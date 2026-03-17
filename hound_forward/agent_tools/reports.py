from __future__ import annotations

from typing import Any

from .common import SCHEMA_VERSION, read_json


def generate_report(input_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    metrics_payload = read_json(input_path)
    cfg = dict(config or {})
    metrics = metrics_payload.get("metrics") or {}
    asymmetry = metrics.get("asymmetry_index")
    recommendations: list[str] = []
    if asymmetry is not None and asymmetry > 0.12:
        recommendations.append("Review asymmetry before promoting this run into a production validation cohort.")
    else:
        recommendations.append("Metric profile is stable enough to continue with the current agent-designed tool chain.")
    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "tool": "generate_report",
            "title": cfg.get("title", "Agent Tool Report"),
            "status": "completed",
            "recommendations": recommendations,
        },
        "report": {
            "metrics": metrics,
            "recommendations": recommendations,
            "provenance": metrics_payload.get("summary") or {},
        },
    }

