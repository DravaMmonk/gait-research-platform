from __future__ import annotations

from typing import Any

import numpy as np

from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.core.registry import registry


def build_signals_for_video(
    video_id: str,
    config: dict[str, Any],
    data_manager: DataManager,
) -> dict[str, np.ndarray]:
    pose_data = data_manager.ensure_pose(video_id)
    outputs: dict[str, np.ndarray] = {}
    cache_signals = bool(config["data"].get("cache_signals", True))

    for signal_config in config["signals"]:
        if not signal_config.get("enabled", True):
            continue
        signal_name = signal_config["name"]
        signal_path = data_manager.signal_path(video_id, signal_name)
        if cache_signals and signal_path.exists():
            cached = data_manager.load_signal(video_id, signal_name)
            feature_columns = [column for column in cached.columns if column not in {"video_id", "signal_name", "frame_index"}]
            outputs[signal_name] = cached[feature_columns].to_numpy(dtype=np.float32)
            continue

        signal_cls = registry.get_from_category("signals", signal_name)
        signal = signal_cls(**signal_config.get("params", {}))
        features = signal.build(video_id, pose_data)
        outputs[signal_name] = features
        if cache_signals:
            data_manager.save_signal(video_id, signal_name, features)
    return outputs


def concatenate_signals(signals: dict[str, np.ndarray]) -> np.ndarray:
    if not signals:
        raise ValueError("No enabled signals were produced.")
    matrices = list(signals.values())
    lengths = {matrix.shape[0] for matrix in matrices}
    if len(lengths) != 1:
        raise ValueError(f"Signal lengths do not match: {sorted(lengths)}")
    return np.concatenate(matrices, axis=1).astype(np.float32)
