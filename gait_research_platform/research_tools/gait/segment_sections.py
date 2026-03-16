from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.common.dataframe_adapter import FPS
from research_tools.common.io_models import sections_payload
from research_tools.common.paths import read_json, write_json


LATERAL = {"left_to_right", "right_to_left"}


@dataclass(frozen=True)
class Section:
    section_id: int
    direction: str
    visible_side: str | None
    start_frame: int
    end_frame: int
    frame_count: int
    duration_seconds: float
    confidence_avg: float
    fps: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "direction": self.direction,
            "visible_side": self.visible_side,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "frame_count": self.frame_count,
            "duration_seconds": self.duration_seconds,
            "confidence_avg": self.confidence_avg,
            "fps": self.fps,
        }


def segment_sections(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = read_json(input_path)
    config = dict(config or {})
    fps = float(payload.get("summary", {}).get("fps") or config.get("fps") or FPS)
    min_duration_seconds = float(config.get("min_duration_seconds", 0.5))
    min_frames = max(1, int(round(min_duration_seconds * fps)))
    sections = _segment(payload.get("frames") or [], fps=fps, min_frames=min_frames)
    artifact = sections_payload(
        sections=[section.to_dict() for section in sections],
        summary={
            "tool": "segment_sections",
            "section_count": len(sections),
            "fps": fps,
            "min_duration_seconds": min_duration_seconds,
        },
    )
    write_json(output_path, artifact)
    return {"tool": "segment_sections", "output_path": output_path, "section_count": len(sections)}


def _segment(frames: list[dict[str, Any]], *, fps: float, min_frames: int) -> list[Section]:
    sections: list[Section] = []
    current: list[dict[str, Any]] = []
    current_direction: str | None = None
    for frame in frames:
        direction = str(frame.get("direction") or "stationary")
        if direction not in LATERAL:
            if current_direction is not None:
                _flush(sections, current, current_direction, fps, min_frames)
                current, current_direction = [], None
            continue
        if current_direction is None or direction == current_direction:
            current.append(frame)
            current_direction = direction
            continue
        _flush(sections, current, current_direction, fps, min_frames)
        current = [frame]
        current_direction = direction
    if current_direction is not None:
        _flush(sections, current, current_direction, fps, min_frames)
    return sections


def _flush(
    sections: list[Section],
    frames: list[dict[str, Any]],
    direction: str,
    fps: float,
    min_frames: int,
) -> None:
    if len(frames) < min_frames:
        return
    start = int(frames[0]["frame_idx"])
    end = int(frames[-1]["frame_idx"])
    frame_count = end - start + 1
    confidence_avg = round(sum(float(frame.get("confidence", 0.0)) for frame in frames) / len(frames), 4)
    visible_side = "right" if direction == "left_to_right" else "left"
    sections.append(
        Section(
            section_id=len(sections),
            direction=direction,
            visible_side=visible_side,
            start_frame=start,
            end_frame=end,
            frame_count=frame_count,
            duration_seconds=round(frame_count / fps, 3),
            confidence_avg=confidence_avg,
            fps=fps,
        )
    )


if __name__ == "__main__":
    run_cli("segment_sections", segment_sections)
