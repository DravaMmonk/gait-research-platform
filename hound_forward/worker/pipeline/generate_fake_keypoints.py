from __future__ import annotations

from hashlib import sha256

from hound_forward.domain import AssetRecord, RunRecord


def generate_fake_keypoints(*, video_asset: AssetRecord, run: RunRecord) -> dict:
    seed = sha256(f"{run.manifest.id}:{video_asset.asset_id}:{video_asset.checksum}".encode("utf-8")).hexdigest()
    frame_count = max(8, int(video_asset.metadata.get("size_bytes", 1024)) % 12 + 8)
    return {
        "source_video_asset_id": video_asset.asset_id,
        "placeholder_type": "dummy",
        "fake": True,
        "frames": [
            {
                "frame_index": frame_index,
                "hip_left_x": round(0.4 + (int(seed[frame_index : frame_index + 4], 16) % 100) / 1000, 4),
                "hip_right_x": round(0.6 - (int(seed[frame_index : frame_index + 4], 16) % 100) / 2000, 4),
                "head_y": round(0.2 + (int(seed[frame_index : frame_index + 4], 16) % 100) / 3000, 4),
            }
            for frame_index in range(frame_count)
        ],
    }
