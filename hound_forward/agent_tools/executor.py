from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from hound_forward.domain import AssetKind, AssetRecord
from hound_forward.ports import ArtifactStore, ToolRunner

from .metrics import compute_gait_metrics
from .pose import extract_keypoints
from .reports import generate_report
from .symbolic import summarize_manifest
from .video import decode_video


ToolHandler = Callable[[str, dict[str, Any] | None], dict[str, Any]]


@dataclass(frozen=True)
class AgentToolDefinition:
    name: str
    description: str
    input_kind: str
    output_kind: str
    output_name: str
    handler: ToolHandler


class AgentToolExecutor(ToolRunner):
    def __init__(self, artifact_store: ArtifactStore, work_root: Path) -> None:
        self.artifact_store = artifact_store
        self.work_root = work_root
        self.work_root.mkdir(parents=True, exist_ok=True)
        self._registry: dict[str, AgentToolDefinition] = {
            "decode_video": AgentToolDefinition(
                name="decode_video",
                description="Probe uploaded video metadata before downstream analysis.",
                input_kind=AssetKind.VIDEO.value,
                output_kind=AssetKind.REPORT.value,
                output_name="decoded_video.json",
                handler=decode_video,
            ),
            "extract_keypoints": AgentToolDefinition(
                name="extract_keypoints",
                description="Generate keypoint-like motion frames from a video asset.",
                input_kind=AssetKind.VIDEO.value,
                output_kind=AssetKind.KEYPOINTS.value,
                output_name="keypoints.json",
                handler=extract_keypoints,
            ),
            "compute_gait_metrics": AgentToolDefinition(
                name="compute_gait_metrics",
                description="Compute gait metrics from extracted keypoint frames.",
                input_kind=AssetKind.KEYPOINTS.value,
                output_kind=AssetKind.METRIC_RESULT.value,
                output_name="metrics.json",
                handler=compute_gait_metrics,
            ),
            "generate_report": AgentToolDefinition(
                name="generate_report",
                description="Assemble a report from metric outputs.",
                input_kind=AssetKind.METRIC_RESULT.value,
                output_kind=AssetKind.REPORT.value,
                output_name="report.json",
                handler=generate_report,
            ),
            "visualize_pysr_manifest": AgentToolDefinition(
                name="visualize_pysr_manifest",
                description="Summarize a symbolic manifest for review and governance.",
                input_kind=AssetKind.MANIFEST.value,
                output_kind=AssetKind.REPORT.value,
                output_name="manifest_review.json",
                handler=lambda input_path, _config: summarize_manifest(_read_manifest(input_path)),
            ),
        }

    def invoke(
        self,
        *,
        tool_name: str,
        input_asset: AssetRecord,
        run_id: str,
        config: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], AssetRecord]:
        definition = self._registry.get(tool_name)
        if definition is None:
            raise KeyError(f"Unsupported agent tool: {tool_name}")
        if input_asset.kind.value != definition.input_kind:
            raise ValueError(
                f"Tool {tool_name} requires input kind {definition.input_kind}, received {input_asset.kind.value}."
            )
        payload = definition.handler(input_asset.blob_path, dict(config or {}))
        asset = self.artifact_store.put_json(run_id, definition.output_name, payload, definition.output_kind)
        asset.metadata.update(
            {
                "tool_name": tool_name,
                "input_asset_id": input_asset.asset_id,
                "input_kind": input_asset.kind.value,
                "output_kind": definition.output_kind,
            }
        )
        return payload, asset

    def describe_tools(self) -> list[dict[str, str]]:
        return [
            {
                "name": definition.name,
                "description": definition.description,
                "input_kind": definition.input_kind,
                "output_kind": definition.output_kind,
            }
            for definition in self._registry.values()
        ]


def _read_manifest(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
