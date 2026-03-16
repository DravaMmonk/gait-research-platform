from __future__ import annotations

from typing import Any

import numpy as np

from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.common.dataframe_adapter import FrameDirection, FPS, get_likelihood, get_point, keypoints_to_dataframe, smooth
from research_tools.common.io_models import directions_payload
from research_tools.common.paths import read_json, write_json


LEFT_PARTS = [
    "left_shoulder", "left_elbow", "left_wrist", "left_front_paw",
    "left_hip", "left_knee", "left_ankle", "left_hind_paw",
]
RIGHT_PARTS = [
    "right_shoulder", "right_elbow", "right_wrist", "right_front_paw",
    "right_hip", "right_knee", "right_ankle", "right_hind_paw",
]
VELOCITY_PARTS = [
    "nose", "head", "upper_spine", "mid_spine", "lower_spine",
    "pelvis", "tail_base", "left_shoulder", "right_shoulder", "left_hip", "right_hip",
]


def detect_direction(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = read_json(input_path)
    fps = float(payload.get("fps") or (config or {}).get("fps") or FPS)
    df = keypoints_to_dataframe(payload.get("keypoints") or {})
    if df.empty:
        raise RuntimeError("detect_direction requires non-empty keypoints.")
    scorer = str(df.columns.get_level_values(0)[0])
    frames = [frame.__dict__ for frame in _detect(df, scorer, fps)]
    summary = {
        "tool": "detect_direction",
        "frame_count": len(frames),
        "direction_counts": _count_directions(frames),
        "fps": fps,
    }
    artifact = directions_payload(frames=frames, summary=summary)
    write_json(output_path, artifact)
    return {"tool": "detect_direction", "output_path": output_path, "frame_count": len(frames)}


def _detect(df, scorer: str, fps: float) -> list[FrameDirection]:
    left_visibility = _mean_visibility(df, scorer, LEFT_PARTS)
    right_visibility = _mean_visibility(df, scorer, RIGHT_PARTS)
    com_x = _com_x(df, scorer)
    x_velocity = smooth(np.diff(com_x, prepend=com_x[0]), window=11)
    shoulder_width = _distance(df, scorer, "left_shoulder", "right_shoulder")
    hip_width = _distance(df, scorer, "left_hip", "right_hip")
    body_width = np.nanmedian(np.vstack([shoulder_width, hip_width]), axis=0)
    width_median = float(np.nanmedian(body_width[np.isfinite(body_width)])) if np.isfinite(body_width).any() else 1.0
    velocity_threshold = max(np.nanstd(x_velocity) * 0.35, 0.5)

    result: list[FrameDirection] = []
    for frame_idx in range(len(df)):
        facing = "unknown"
        analyzable = True
        confidence = 0.6
        if not np.isfinite(x_velocity[frame_idx]):
            direction = "stationary"
            analyzable = False
            confidence = 0.0
        elif abs(x_velocity[frame_idx]) < velocity_threshold:
            direction = "stationary"
            confidence = 0.4
        elif body_width[frame_idx] < width_median * 0.55:
            direction = "towards_camera" if x_velocity[frame_idx] >= 0 else "away_from_camera"
            facing = "front"
            analyzable = False
            confidence = 0.55
        else:
            direction = "left_to_right" if x_velocity[frame_idx] >= 0 else "right_to_left"
            facing = "right" if direction == "left_to_right" else "left"
            confidence = min(0.99, 0.55 + abs(float(x_velocity[frame_idx])) / max(width_median, 1.0))
        result.append(
            FrameDirection(
                frame_idx=frame_idx,
                direction=direction,
                confidence=float(round(confidence, 4)),
                is_analyzable=analyzable and direction in {"left_to_right", "right_to_left"},
                left_visibility=float(round(left_visibility[frame_idx], 4)),
                right_visibility=float(round(right_visibility[frame_idx], 4)),
                facing=facing,
                x_velocity=float(round(x_velocity[frame_idx], 4)),
            )
        )
    return result


def _mean_visibility(df, scorer: str, parts: list[str]) -> np.ndarray:
    arrays = [get_likelihood(df, scorer, part) for part in parts]
    valid = [arr for arr in arrays if arr is not None]
    if not valid:
        return np.zeros(len(df))
    return np.mean(valid, axis=0)


def _com_x(df, scorer: str) -> np.ndarray:
    weighted_x = np.zeros(len(df))
    weights = np.zeros(len(df))
    for part in VELOCITY_PARTS:
        x, _ = get_point(df, scorer, part)
        likelihood = get_likelihood(df, scorer, part)
        if x is None or likelihood is None:
            continue
        valid = np.isfinite(x)
        weighted_x[valid] += x[valid] * likelihood[valid]
        weights[valid] += likelihood[valid]
    com = np.where(weights > 0, weighted_x / weights, np.nan)
    idx = np.arange(len(df))
    finite = np.isfinite(com)
    if finite.sum() > 2:
        com = np.interp(idx, idx[finite], com[finite])
    else:
        com = np.nan_to_num(com, nan=0.0)
    return smooth(com, window=11)


def _distance(df, scorer: str, first: str, second: str) -> np.ndarray:
    first_x, first_y = get_point(df, scorer, first)
    second_x, second_y = get_point(df, scorer, second)
    if first_x is None or second_x is None:
        return np.full(len(df), np.nan)
    return np.sqrt((second_x - first_x) ** 2 + (second_y - first_y) ** 2)


def _count_directions(frames: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for frame in frames:
        direction = str(frame.get("direction") or "unknown")
        counts[direction] = counts.get(direction, 0) + 1
    return counts


if __name__ == "__main__":
    run_cli("detect_direction", detect_direction)
