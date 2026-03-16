from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, TypedDict


SCHEMA_VERSION = "v1"


class FramePoint(TypedDict, total=False):
    x: float | None
    y: float | None
    c: float | None


KeypointsDataset = dict[str, list[FramePoint]]


@dataclass(frozen=True)
class ArtifactSummary:
    tool: str
    schema_version: str = SCHEMA_VERSION
    input_path: str | None = None
    output_path: str | None = None
    frame_count: int | None = None
    section_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def keypoints_payload(
    *,
    keypoints: KeypointsDataset,
    fps: float,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "keypoints": keypoints,
        "fps": float(fps),
        "metadata": dict(metadata or {}),
    }


def directions_payload(
    *,
    frames: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "frames": frames, "summary": summary}


def sections_payload(
    *,
    sections: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "sections": sections, "summary": summary}


def stride_payload(
    *,
    sections: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "sections": sections, "summary": summary}


def metrics_payload(
    *,
    metrics: dict[str, Any],
    sections: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "metrics": metrics,
        "sections": sections,
        "summary": summary,
    }


def report_payload(
    *,
    report: dict[str, Any],
    inputs: dict[str, Any],
) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "report": report, "inputs": inputs}

