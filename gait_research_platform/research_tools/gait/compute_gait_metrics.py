from __future__ import annotations

from typing import Any

import numpy as np

from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.common.dataframe_adapter import FPS, JOINTS, SIDE_LEGS, calc_angle, get_point, keypoints_to_dataframe
from research_tools.common.io_models import metrics_payload
from research_tools.common.paths import read_json, write_json


JOINT_DEFINITIONS = {
    "shoulder": {"left": ("upper_spine", "left_shoulder", "left_elbow"), "right": ("upper_spine", "right_shoulder", "right_elbow")},
    "elbow": {"left": ("left_shoulder", "left_elbow", "left_wrist"), "right": ("right_shoulder", "right_elbow", "right_wrist")},
    "stifle": {"left": ("left_hip", "left_knee", "left_ankle"), "right": ("right_hip", "right_knee", "right_ankle")},
    "hock": {"left": ("left_knee", "left_ankle", "left_hind_paw"), "right": ("right_knee", "right_ankle", "right_hind_paw")},
}


def compute_gait_metrics(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = dict(config or {})
    keypoints_payload = read_json(input_path)
    sections_path = config.get("sections_path")
    stride_path = config.get("stride_path")
    if not sections_path or not stride_path:
        raise RuntimeError("compute_gait_metrics requires config['sections_path'] and config['stride_path'].")
    sections_json = read_json(sections_path)
    stride_json = read_json(stride_path)
    fps = float(keypoints_payload.get("fps") or config.get("fps") or FPS)
    df = keypoints_to_dataframe(keypoints_payload.get("keypoints") or {})
    if df.empty:
        raise RuntimeError("compute_gait_metrics requires non-empty keypoints.")
    scorer = str(df.columns.get_level_values(0)[0])
    stride_sections = {int(section["section_id"]): section for section in stride_json.get("sections") or []}
    metric_sections = []
    for section in sections_json.get("sections") or []:
        stride_section = stride_sections.get(int(section["section_id"]))
        metric_sections.append(_section_metrics(df, scorer, fps, section, stride_section))
    summary = _build_summary(metric_sections)
    metrics = {
        "stride_analysis": stride_json.get("summary") or {},
        "joint_analysis": summary["joint_summary"],
        "symmetry": summary["symmetry"],
    }
    artifact = metrics_payload(metrics=metrics, sections=metric_sections, summary=summary["summary"])
    write_json(output_path, artifact)
    return {"tool": "compute_gait_metrics", "output_path": output_path, "section_count": len(metric_sections)}


def _section_metrics(df, scorer: str, fps: float, section: dict[str, Any], stride_section: dict[str, Any] | None) -> dict[str, Any]:
    start = int(section["start_frame"])
    end = int(section["end_frame"])
    visible_side = section.get("visible_side")
    section_df = df.iloc[start : end + 1].reset_index(drop=True)
    rom_data: dict[str, Any] = {}
    limb_load = {}
    if visible_side in SIDE_LEGS:
        for joint_name in JOINTS:
            rom = _joint_rom(section_df, scorer, joint_name, visible_side)
            if rom:
                rom_data[f"{visible_side}_{joint_name}"] = rom
        if stride_section:
            for leg_name in SIDE_LEGS[visible_side]:
                leg = (stride_section.get("legs") or {}).get(leg_name)
                if leg:
                    limb_load[leg_name] = {
                        "limb_name": leg_name,
                        "duty_factor": leg.get("duty_factor"),
                        "stance_percentage": leg.get("duty_factor"),
                        "swing_percentage": round(100.0 - float(leg.get("duty_factor") or 0.0), 2),
                    }
    return {
        "section_id": int(section["section_id"]),
        "direction": section["direction"],
        "visible_side": visible_side,
        "start_frame": start,
        "end_frame": end,
        "frame_count": int(section["frame_count"]),
        "duration_seconds": float(section["duration_seconds"]),
        "rom_data": rom_data,
        "limb_load_data": limb_load,
        "stride": stride_section,
    }


def _joint_rom(df, scorer: str, joint_name: str, side: str) -> dict[str, Any] | None:
    parts = JOINT_DEFINITIONS.get(joint_name, {}).get(side)
    if not parts:
        return None
    p1_x, p1_y = get_point(df, scorer, parts[0])
    p2_x, p2_y = get_point(df, scorer, parts[1])
    p3_x, p3_y = get_point(df, scorer, parts[2])
    if any(item is None for item in (p1_x, p1_y, p2_x, p2_y, p3_x, p3_y)):
        return None
    angles = calc_angle(p1_x, p1_y, p2_x, p2_y, p3_x, p3_y)
    finite = angles[np.isfinite(angles)]
    if len(finite) < 3:
        return None
    return {
        "joint_name": joint_name,
        "side": side,
        "min_flexion": round(float(np.nanpercentile(angles, 5)), 2),
        "max_extension": round(float(np.nanpercentile(angles, 95)), 2),
        "total_rom": round(float(np.nanpercentile(angles, 95) - np.nanpercentile(angles, 5)), 2),
        "mean_angle": round(float(np.nanmean(angles)), 2),
    }


def _build_summary(metric_sections: list[dict[str, Any]]) -> dict[str, Any]:
    limb_duty: dict[str, list[float]] = {}
    joint_roms: dict[str, list[float]] = {}
    for section in metric_sections:
        for leg_name, limb in (section.get("limb_load_data") or {}).items():
            limb_duty.setdefault(leg_name, []).append(float(limb.get("duty_factor") or 0.0))
        for joint_key, rom in (section.get("rom_data") or {}).items():
            joint_roms.setdefault(joint_key, []).append(float(rom.get("total_rom") or 0.0))
    joint_summary = {joint: {"avg_total_rom": round(float(np.mean(values)), 2), "section_count": len(values)} for joint, values in joint_roms.items()}
    symmetry = {
        "front_symmetry": _symmetry_index(limb_duty.get("front_left"), limb_duty.get("front_right")),
        "hind_symmetry": _symmetry_index(limb_duty.get("back_left"), limb_duty.get("back_right")),
    }
    summary = {
        "tool": "compute_gait_metrics",
        "section_count": len(metric_sections),
        "joint_summary": joint_summary,
        "symmetry": symmetry,
    }
    return {"summary": summary, "joint_summary": joint_summary, "symmetry": symmetry}


def _symmetry_index(left: list[float] | None, right: list[float] | None) -> float | None:
    if not left or not right:
        return None
    left_avg = float(np.mean(left))
    right_avg = float(np.mean(right))
    denom = max(abs(left_avg) + abs(right_avg), 1e-6)
    return round(abs(left_avg - right_avg) / (denom / 2.0) * 100.0, 2)


if __name__ == "__main__":
    run_cli("compute_gait_metrics", compute_gait_metrics)
