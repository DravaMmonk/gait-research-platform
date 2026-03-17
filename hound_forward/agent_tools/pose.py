from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from .common import SCHEMA_VERSION, require_file


def extract_keypoints(input_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    video_path = require_file(input_path)
    cfg = dict(config or {})
    if "mock_payload" in cfg:
        payload = dict(cfg["mock_payload"])
        payload.setdefault("schema_version", SCHEMA_VERSION)
        return payload

    seed = sha256(f"{video_path}:{video_path.stat().st_size}:{json.dumps(cfg, sort_keys=True)}".encode("utf-8")).hexdigest()
    frame_count = max(8, int(video_path.stat().st_size) % 12 + 8)
    frames = [
        {
            "frame_index": frame_index,
            "hip_left_x": round(0.4 + (int(seed[frame_index : frame_index + 4], 16) % 100) / 1000, 4),
            "hip_right_x": round(0.6 - (int(seed[frame_index : frame_index + 4], 16) % 100) / 2000, 4),
            "head_y": round(0.2 + (int(seed[frame_index : frame_index + 4], 16) % 100) / 3000, 4),
        }
        for frame_index in range(frame_count)
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_video_path": str(video_path),
        "frame_count": frame_count,
        "frames": frames,
        "metadata": {"tool": "extract_keypoints", "mode": cfg.get("mode", "agent_scaffold")},
    }

