from __future__ import annotations

import numpy as np
import pandas as pd

from gait_research_platform.core.interfaces import Signal
from gait_research_platform.core.registry import register_signal
from gait_research_platform.utils.pose_utils import get_feature_columns


@register_signal("velocity_signal")
class VelocitySignal(Signal):
    name = "velocity_signal"

    def build(self, video_id: str, pose_data: pd.DataFrame) -> np.ndarray:
        del video_id
        columns = get_feature_columns(pose_data)
        positions = pose_data[columns].to_numpy(dtype=np.float32)
        velocity = np.diff(positions, axis=0, prepend=positions[:1])
        if self.params.get("normalize", True):
            std = velocity.std(axis=0, keepdims=True)
            std[std < 1e-6] = 1.0
            velocity = (velocity - velocity.mean(axis=0, keepdims=True)) / std
        return velocity.astype(np.float32)
