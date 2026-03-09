from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


JOINTS = ["hip", "knee", "ankle"]
AXES = ["x", "y"]


def generate_sample_pose_dataset(output_dir: str | Path, num_videos: int = 6, num_frames: int = 64) -> list[Path]:
    base_dir = Path(output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for video_index in range(num_videos):
        phase = video_index * 0.35
        frames = np.arange(num_frames, dtype=np.float32)
        rows: dict[str, np.ndarray] = {"frame_index": frames.astype(int)}
        for joint_idx, joint in enumerate(JOINTS):
            frequency = 0.12 + joint_idx * 0.03
            rows[f"{joint}_x"] = np.sin(frames * frequency + phase) + joint_idx * 0.5
            rows[f"{joint}_y"] = np.cos(frames * frequency + phase) + joint_idx * 0.2

        pose_df = pd.DataFrame(rows)
        path = base_dir / f"sample_{video_index:02d}.parquet"
        pose_df.to_parquet(path, index=False)
        generated.append(path)
    return generated
