from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from research_tools.common.io_models import KeypointsDataset


P_CUTOFF = 0.4
EPSILON = 1e-6
FPS = 30.0
LEG_COLORS = {
    "front_left": "#E65100",
    "front_right": "#9E9D24",
    "back_left": "#00897B",
    "back_right": "#0277BD",
}
SIDE_LEGS = {
    "left": ["front_left", "back_left"],
    "right": ["front_right", "back_right"],
}
JOINTS = ["shoulder", "elbow", "stifle", "hock"]


@dataclass(frozen=True)
class FrameDirection:
    frame_idx: int
    direction: str
    confidence: float
    is_analyzable: bool
    left_visibility: float
    right_visibility: float
    facing: str
    x_velocity: float = 0.0


def keypoints_to_dataframe(keypoints: KeypointsDataset, scorer: str = "scorer") -> pd.DataFrame:
    if not keypoints:
        return pd.DataFrame()
    keypoint_names = list(keypoints.keys())
    if not keypoint_names:
        return pd.DataFrame()
    frame_count = max(len(points) for points in keypoints.values())
    coord_order = ["x", "y", "likelihood"]
    columns = pd.MultiIndex.from_product([[scorer], keypoint_names, coord_order])
    data = np.full((frame_count, len(keypoint_names) * len(coord_order)), np.nan)
    for part_idx, part_name in enumerate(keypoint_names):
        part_data = keypoints.get(part_name, [])
        for frame_idx in range(frame_count):
            point = part_data[frame_idx] if frame_idx < len(part_data) else {}
            if isinstance(point, dict):
                data[frame_idx, part_idx * len(coord_order)] = _float_or_nan(point.get("x"))
                data[frame_idx, part_idx * len(coord_order) + 1] = _float_or_nan(point.get("y"))
                data[frame_idx, part_idx * len(coord_order) + 2] = _float_or_nan(
                    point.get("c", point.get("likelihood"))
                )
    return pd.DataFrame(data, columns=columns)


def dataframe_to_keypoints(df: pd.DataFrame, scorer: str | None = None) -> KeypointsDataset:
    if df.empty:
        return {}
    scorer_name = scorer or str(df.columns.get_level_values(0)[0])
    payload: KeypointsDataset = {}
    for part in df[scorer_name].columns.get_level_values(0).unique():
        series: list[dict[str, float | None]] = []
        for _, row in df[scorer_name][part].iterrows():
            series.append(
                {
                    "x": _nan_to_none(row.get("x")),
                    "y": _nan_to_none(row.get("y")),
                    "c": _nan_to_none(row.get("likelihood")),
                }
            )
        payload[str(part)] = series
    return payload


def smooth(signal: np.ndarray, window: int = 7) -> np.ndarray:
    from scipy.signal import savgol_filter

    if len(signal) < window:
        return signal
    if window % 2 == 0:
        window += 1
    bad_mask = ~np.isfinite(signal)
    if np.any(bad_mask):
        good_mask = np.isfinite(signal)
        if not np.any(good_mask):
            return signal.copy()
        clean = signal.copy()
        good_indices = np.where(good_mask)[0]
        bad_indices = np.where(bad_mask)[0]
        clean[bad_mask] = np.interp(bad_indices, good_indices, signal[good_mask])
        result = savgol_filter(clean, window, polyorder=3)
        result[bad_mask] = np.nan
        return result
    return savgol_filter(signal, window, polyorder=3)


def normalize_signal(signal: np.ndarray, low_pct: float = 5.0, high_pct: float = 95.0) -> np.ndarray:
    if len(signal) == 0 or np.all(np.isnan(signal)):
        return np.ones(max(len(signal), 1)) * 0.5
    valid_signal = signal[~np.isnan(signal)]
    if len(valid_signal) < 2:
        return np.ones_like(signal) * 0.5
    p_lo, p_hi = np.nanpercentile(signal, [low_pct, high_pct])
    if p_hi - p_lo < 1e-6:
        return np.ones_like(signal) * 0.5
    normalized = (signal - p_lo) / (p_hi - p_lo)
    normalized = np.where(np.isnan(normalized), 0.5, normalized)
    return np.clip(normalized, 0, 1)


def get_likelihood(df: pd.DataFrame, scorer: str, part: str) -> np.ndarray | None:
    if part not in df[scorer]:
        return None
    try:
        return df[scorer][part]["likelihood"].values.astype(float)
    except KeyError:
        return None


def get_point(df: pd.DataFrame, scorer: str, part: str) -> tuple[np.ndarray | None, np.ndarray | None]:
    if part not in df[scorer]:
        return None, None
    x = df[scorer][part]["x"].values.astype(float)
    y = df[scorer][part]["y"].values.astype(float)
    likelihood = df[scorer][part]["likelihood"].values.astype(float)
    valid = likelihood > P_CUTOFF
    if valid.sum() > 2:
        valid_indices = np.where(valid)[0]
        invalid_indices = np.where(~valid)[0]
        x[~valid] = np.interp(invalid_indices, valid_indices, x[valid])
        y[~valid] = np.interp(invalid_indices, valid_indices, y[valid])
    return x, y


def calc_angle(
    p1_x: np.ndarray,
    p1_y: np.ndarray,
    p2_x: np.ndarray,
    p2_y: np.ndarray,
    p3_x: np.ndarray,
    p3_y: np.ndarray,
) -> np.ndarray:
    v1 = np.stack([p1_x - p2_x, p1_y - p2_y], axis=1)
    v2 = np.stack([p3_x - p2_x, p3_y - p2_y], axis=1)
    norm1 = np.linalg.norm(v1, axis=1)
    norm2 = np.linalg.norm(v2, axis=1)
    denom = np.maximum(norm1 * norm2, EPSILON)
    cos_angle = np.sum(v1 * v2, axis=1) / denom
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))


def compute_body_length(df: pd.DataFrame, scorer: str, start_frame: int = 0, end_frame: int | None = None) -> float:
    spine_pairs = [("nose", "tail_base"), ("upper_spine", "tail_base"), ("head", "pelvis")]
    measurements: list[float] = []
    end = end_frame if end_frame is not None else len(df) - 1
    for first, second in spine_pairs:
        first_x, first_y = get_point(df, scorer, first)
        second_x, second_y = get_point(df, scorer, second)
        if first_x is None or second_x is None:
            continue
        dx = second_x[start_frame : end + 1] - first_x[start_frame : end + 1]
        dy = second_y[start_frame : end + 1] - first_y[start_frame : end + 1]
        dist = np.sqrt(dx**2 + dy**2)
        valid = dist[np.isfinite(dist)]
        if len(valid):
            measurements.append(float(np.nanmedian(valid)))
    return float(np.nanmedian(measurements)) if measurements else 1.0


def make_time_axis(n_frames: int, fps: float) -> list[float]:
    return [round(i / fps, 4) for i in range(n_frames)]


def weighted_avg(values: list[float], weights: list[float]) -> float | None:
    if not values or not weights or len(values) != len(weights):
        return None
    pairs = [
        (v, w)
        for v, w in zip(values, weights)
        if v is not None and w is not None and np.isfinite(v) and np.isfinite(w) and w > 0
    ]
    if not pairs:
        return None
    vs, ws = zip(*pairs)
    return round(float(np.average(vs, weights=ws)), 4)


def safe_avg(values: list[float]) -> float | None:
    if not values:
        return None
    cleaned = [float(v) for v in values if v is not None and np.isfinite(v)]
    return round(float(np.mean(cleaned)), 4) if cleaned else None


def _float_or_nan(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _nan_to_none(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(numeric) else numeric

