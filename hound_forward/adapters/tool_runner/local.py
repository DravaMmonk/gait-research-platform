from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Callable

from hound_forward.domain import AssetKind, AssetRecord
from hound_forward.ports import ArtifactStore, ToolRunner


ToolFn = Callable[[str, str, dict | None], dict]


class LocalResearchToolRunner(ToolRunner):
    """Execute research_tools against local staged files and register JSON outputs as artifacts."""

    def __init__(self, artifact_store: ArtifactStore, work_root: Path) -> None:
        self.artifact_store = artifact_store
        self.work_root = work_root
        self.work_root.mkdir(parents=True, exist_ok=True)
        self._registry = {
            "decode_video": ("research_tools.video.decode_video", "decode_video", AssetKind.REPORT),
            "extract_keypoints": ("research_tools.pose.extract_keypoints", "extract_keypoints", AssetKind.KEYPOINTS),
            "compute_gait_metrics": ("research_tools.gait.compute_gait_metrics", "compute_gait_metrics", AssetKind.METRIC_RESULT),
            "generate_report": ("research_tools.reports.generate_report", "generate_report", AssetKind.REPORT),
        }

    def invoke(
        self,
        *,
        tool_name: str,
        input_asset: AssetRecord,
        run_id: str,
        config: dict | None = None,
    ) -> tuple[dict, AssetRecord]:
        if tool_name not in self._registry:
            raise KeyError(f"Unsupported research tool: {tool_name}")
        module_name, attribute_name, asset_kind = self._registry[tool_name]
        tool_fn = getattr(importlib.import_module(module_name), attribute_name)
        input_path = Path(input_asset.blob_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Tool input asset path not found: {input_path}")
        output_name = f"{tool_name}.json"
        output_path = self.work_root / run_id / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = tool_fn(str(input_path), str(output_path), dict(config or {}))
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        asset = self.artifact_store.put_json(run_id, output_name, payload, asset_kind.value)
        asset.metadata.update(
            {
                "tool_name": tool_name,
                "tool_result": result,
                "placeholder_flags": {"dummy": False, "fake": False, "placeholder": False},
            }
        )
        return result, asset
