from __future__ import annotations

from typing import Iterable

import pandas as pd


def get_feature_columns(pose_data: pd.DataFrame) -> list[str]:
    excluded = {"video_id", "frame_index"}
    return [column for column in pose_data.columns if column not in excluded]


def ensure_pose_columns(pose_data: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [column for column in required if column not in pose_data.columns]
    if missing:
        raise ValueError(f"Pose data is missing required columns: {missing}")
