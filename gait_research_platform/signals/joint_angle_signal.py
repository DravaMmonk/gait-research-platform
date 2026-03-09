from __future__ import annotations

import pandas as pd

from gait_research_platform.core.interfaces import Signal
from gait_research_platform.core.registry import register_signal


@register_signal("joint_angle_signal")
class JointAngleSignal(Signal):
    name = "joint_angle_signal"

    def build(self, video_id: str, pose_data: pd.DataFrame):
        del video_id, pose_data
        raise NotImplementedError("joint_angle_signal is reserved for a future extension.")
