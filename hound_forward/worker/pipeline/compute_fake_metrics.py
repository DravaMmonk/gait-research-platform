from __future__ import annotations

import json
from hashlib import sha256

from hound_forward.domain import AssetRecord, RunRecord


def compute_fake_metrics(*, video_asset: AssetRecord, run: RunRecord, keypoints: dict) -> dict:
    seed = sha256(
        f"{run.manifest.id}:{video_asset.asset_id}:{json.dumps(keypoints['frames'][:3], sort_keys=True)}".encode("utf-8")
    ).hexdigest()
    return {
        "stride_length": round(0.7 + (int(seed[:4], 16) % 25) / 100, 4),
        "asymmetry_index": round(0.05 + (int(seed[4:8], 16) % 20) / 100, 4),
        "placeholder_type": "fake",
        "fake": True,
        "source_video_asset_id": video_asset.asset_id,
    }
