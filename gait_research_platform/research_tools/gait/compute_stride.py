from __future__ import annotations

from typing import Any

import numpy as np
from scipy.signal import find_peaks

from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.common.dataframe_adapter import FPS, LEG_COLORS, SIDE_LEGS, compute_body_length, get_likelihood, get_point, keypoints_to_dataframe, make_time_axis, normalize_signal
from research_tools.common.io_models import stride_payload
from research_tools.common.paths import read_json, write_json


def compute_stride(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = dict(config or {})
    keypoints_payload = read_json(input_path)
    sections_path = config.get("sections_path")
    if not sections_path:
        raise RuntimeError("compute_stride requires config['sections_path'].")
    sections_payload_json = read_json(sections_path)
    fps = float(keypoints_payload.get("fps") or config.get("fps") or FPS)
    df = keypoints_to_dataframe(keypoints_payload.get("keypoints") or {})
    if df.empty:
        raise RuntimeError("compute_stride requires non-empty keypoints.")
    scorer = str(df.columns.get_level_values(0)[0])
    results = [
        _analyze_section(df, scorer, fps, section, config)
        for section in sections_payload_json.get("sections") or []
    ]
    results = [item for item in results if item is not None]
    summary = {
        "tool": "compute_stride",
        "section_count": len(results),
        "total_strides": sum(sum(leg.get("stride_count", 0) for leg in section.get("legs", {}).values()) for section in results),
        "fps": fps,
    }
    artifact = stride_payload(sections=results, summary=summary)
    write_json(output_path, artifact)
    return {"tool": "compute_stride", "output_path": output_path, "section_count": len(results)}


def _analyze_section(df, scorer: str, fps: float, section: dict[str, Any], config: dict[str, Any]) -> dict[str, Any] | None:
    visible_side = section.get("visible_side")
    if visible_side not in SIDE_LEGS:
        return None
    start = int(section["start_frame"])
    end = int(section["end_frame"])
    section_df = df.iloc[start : end + 1].reset_index(drop=True)
    body_scale = compute_body_length(section_df, scorer)
    legs: dict[str, Any] = {}
    for leg_name in SIDE_LEGS[visible_side]:
        leg_result = _analyze_leg(section_df, scorer, fps, leg_name, body_scale, config)
        if leg_result is not None:
            legs[leg_name] = leg_result
    if not legs:
        return None
    duty_factors = [leg["duty_factor"] for leg in legs.values() if leg.get("duty_factor") is not None]
    front_duty = [legs[name]["duty_factor"] for name in legs if name.startswith("front_")]
    hind_duty = [legs[name]["duty_factor"] for name in legs if name.startswith("back_")]
    return {
        "section_id": section["section_id"],
        "direction": section["direction"],
        "visible_side": visible_side,
        "start_frame": start,
        "end_frame": end,
        "frame_count": int(section["frame_count"]),
        "duration_seconds": float(section["duration_seconds"]),
        "time_axis": make_time_axis(int(section["frame_count"]), fps),
        "legs": legs,
        "front_duty_avg": round(float(np.mean(front_duty)) if front_duty else 0.0, 2),
        "hind_duty_avg": round(float(np.mean(hind_duty)) if hind_duty else 0.0, 2),
        "cadence": round(_estimate_cadence(legs, section["duration_seconds"]), 2),
        "gait_type": _classify_gait(duty_factors),
        "view_quality": "lateral",
    }


def _analyze_leg(df, scorer: str, fps: float, leg_name: str, body_scale: float, config: dict[str, Any]) -> dict[str, Any] | None:
    position, side = leg_name.split("_", 1)
    paw_name = f"{side}_front_paw" if position == "front" else f"{side}_hind_paw"
    ref_name = f"{side}_shoulder" if position == "front" else f"{side}_hip"
    paw_x, paw_y = get_point(df, scorer, paw_name)
    _, ref_y = get_point(df, scorer, ref_name)
    if paw_x is None or paw_y is None:
        return None
    if ref_y is None:
        ref_y = paw_y
    velocity_x = np.diff(paw_x, prepend=paw_x[0]) * fps
    velocity_y = np.diff(paw_y, prepend=paw_y[0]) * fps
    speed = np.sqrt(velocity_x**2 + velocity_y**2) / max(body_scale, 1.0)
    relative_height = (paw_y - ref_y) / max(body_scale, 1.0)
    speed_score = 1.0 - normalize_signal(speed)
    height_score = normalize_signal(relative_height)
    stance_probability = 0.65 * speed_score + 0.35 * height_score
    threshold = float(config.get("stance_threshold", 0.5))
    is_stance = (stance_probability >= threshold).astype(bool)
    peak_distance = max(2, int(fps * float(config.get("peak_min_distance_seconds", 0.25))))
    peaks, _ = find_peaks(-normalize_signal(relative_height), distance=peak_distance)
    stride_count = int(len(peaks))
    stride_lengths = []
    if len(peaks) >= 2:
        for first, second in zip(peaks[:-1], peaks[1:]):
            stride_lengths.append(abs(float(paw_x[second] - paw_x[first])) / max(body_scale, 1.0))
    stance_durations, swing_durations = _phase_durations(is_stance, fps)
    likelihood = get_likelihood(df, scorer, paw_name)
    signal_quality = float(np.nanmean(likelihood)) if likelihood is not None else 0.0
    return {
        "leg_name": leg_name,
        "color": LEG_COLORS.get(leg_name, "#888888"),
        "side": side,
        "position": position,
        "time_axis": make_time_axis(len(is_stance), fps),
        "stance_probability": [round(float(value), 4) for value in stance_probability],
        "is_stance": [bool(value) for value in is_stance],
        "stride_count": stride_count,
        "stance_durations": [round(value, 4) for value in stance_durations],
        "swing_durations": [round(value, 4) for value in swing_durations],
        "duty_factor": round(float(np.mean(is_stance) * 100), 2),
        "avg_stride_length": round(float(np.mean(stride_lengths)), 4) if stride_lengths else None,
        "signal_quality": round(signal_quality, 4),
        "gait_type": None,
        "cadence": round(float(stride_count / max(len(is_stance) / fps, 1e-6) * 60.0), 2),
        "stride_regularity": round(float(np.std(stride_lengths)) if len(stride_lengths) > 1 else 0.0, 4),
        "strides": [{"start_frame": int(peak), "end_frame": int(peak)} for peak in peaks],
    }


def _phase_durations(is_stance: np.ndarray, fps: float) -> tuple[list[float], list[float]]:
    stance: list[float] = []
    swing: list[float] = []
    if len(is_stance) == 0:
        return stance, swing
    current_state = bool(is_stance[0])
    current_len = 1
    for state in is_stance[1:]:
        if bool(state) == current_state:
            current_len += 1
            continue
        duration = current_len / fps
        (stance if current_state else swing).append(duration)
        current_state = bool(state)
        current_len = 1
    duration = current_len / fps
    (stance if current_state else swing).append(duration)
    return stance, swing


def _classify_gait(duty_factors: list[float]) -> str | None:
    if not duty_factors:
        return None
    duty = float(np.mean(duty_factors))
    if duty >= 55.0:
        return "walk"
    if duty >= 38.0:
        return "trot"
    if duty >= 25.0:
        return "canter"
    return "gallop"


def _estimate_cadence(legs: dict[str, Any], duration_seconds: float) -> float:
    if not legs or duration_seconds <= 0:
        return 0.0
    total = sum(float(leg.get("stride_count", 0)) for leg in legs.values())
    return (total / len(legs)) / duration_seconds * 60.0


if __name__ == "__main__":
    run_cli("compute_stride", compute_stride)
