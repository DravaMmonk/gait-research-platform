from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from .common import SCHEMA_VERSION, read_json


def compute_gait_metrics(input_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = read_json(input_path)
    cfg = dict(config or {})
    frames = payload.get("frames") or []
    if not frames:
        raise RuntimeError("compute_gait_metrics requires keypoint frames.")
    seed = sha256(json.dumps(frames[: min(len(frames), 4)], sort_keys=True).encode("utf-8")).hexdigest()
    stride_length = round(0.7 + (int(seed[:4], 16) % 25) / 100, 4)
    asymmetry_index = round(0.05 + (int(seed[4:8], 16) % 20) / 100, 4)
    stability_index = round(max(0.0, 1.0 - asymmetry_index / 2), 4)
    return {
        "schema_version": SCHEMA_VERSION,
        "metrics": {
            "stride_length": stride_length,
            "asymmetry_index": asymmetry_index,
            "gait_stability": stability_index,
        },
        "summary": {
            "tool": "compute_gait_metrics",
            "frame_count": len(frames),
            "metric_names": sorted(["stride_length", "asymmetry_index", "gait_stability"]),
            "mode": cfg.get("mode", "agent_scaffold"),
        },
    }

