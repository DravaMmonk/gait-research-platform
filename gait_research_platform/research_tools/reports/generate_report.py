from __future__ import annotations

from typing import Any

from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.common.io_models import report_payload
from research_tools.common.paths import read_json, write_json


def generate_report(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = dict(config or {})
    gait_metrics = read_json(input_path)
    sections = read_json(config["sections_path"]) if config.get("sections_path") else None
    stride = read_json(config["stride_path"]) if config.get("stride_path") else None
    decoded_video = read_json(config["decoded_video_path"]) if config.get("decoded_video_path") else None
    report = {
        "title": config.get("title", "Gait Research Report"),
        "overview": {
            "section_count": gait_metrics.get("summary", {}).get("section_count"),
            "front_symmetry": (gait_metrics.get("metrics", {}).get("symmetry") or {}).get("front_symmetry"),
            "hind_symmetry": (gait_metrics.get("metrics", {}).get("symmetry") or {}).get("hind_symmetry"),
        },
        "joint_summary": gait_metrics.get("metrics", {}).get("joint_analysis") or {},
        "stride_summary": gait_metrics.get("metrics", {}).get("stride_analysis") or {},
        "recommendations": _recommendations(gait_metrics),
    }
    payload = report_payload(
        report=report,
        inputs={
            "gait_metrics": input_path,
            "sections": config.get("sections_path"),
            "stride": config.get("stride_path"),
            "decoded_video": config.get("decoded_video_path"),
            "video_metadata": decoded_video.get("video") if decoded_video else None,
            "section_count": len((sections or {}).get("sections") or []),
            "stride_sections": len((stride or {}).get("sections") or []),
        },
    )
    write_json(output_path, payload)
    return {"tool": "generate_report", "output_path": output_path, "title": report["title"]}


def _recommendations(gait_metrics: dict[str, Any]) -> list[str]:
    symmetry = gait_metrics.get("metrics", {}).get("symmetry") or {}
    recommendations: list[str] = []
    front = symmetry.get("front_symmetry")
    hind = symmetry.get("hind_symmetry")
    if front is not None and front > 10:
        recommendations.append("Review front-limb asymmetry across lateral sections.")
    if hind is not None and hind > 10:
        recommendations.append("Review hind-limb asymmetry across lateral sections.")
    if not recommendations:
        recommendations.append("No major asymmetry flags were detected in the extracted gait metrics.")
    return recommendations


if __name__ == "__main__":
    run_cli("generate_report", generate_report)
