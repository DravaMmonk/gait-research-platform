from __future__ import annotations

from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.common.io_models import keypoints_payload
from research_tools.common.paths import require_file, write_json


def extract_keypoints(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    video_path = require_file(input_path)
    config = dict(config or {})
    if "mock_payload" in config:
        payload = dict(config["mock_payload"])
    elif config.get("mode") == "legacy_local_dlc":
        payload = _run_legacy_local_dlc(video_path, config)
    else:
        raise RuntimeError(
            "extract_keypoints requires explicit config. Use {'mode': 'legacy_local_dlc', ...} "
            "or provide {'mock_payload': ...} for tests."
        )
    if "schema_version" not in payload:
        payload = keypoints_payload(
            keypoints=payload.get("keypoints") or {},
            fps=float(payload.get("fps") or 0.0),
            metadata=dict(payload.get("metadata") or {}),
        )
    write_json(output_path, payload)
    return {
        "tool": "extract_keypoints",
        "output_path": output_path,
        "keypoint_names": sorted((payload.get("keypoints") or {}).keys()),
        "fps": payload.get("fps"),
    }


def _run_legacy_local_dlc(video_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    from workers.capabilities.extractors.dlc_runner import run_local_dlc_analysis

    result = run_local_dlc_analysis(
        video_bytes=video_path.read_bytes(),
        video_filename=video_path.name,
        project_path=config.get("project_path"),
        config_filename=str(config.get("config_filename") or "config.yaml"),
        provider_config=dict(config.get("provider_config") or {}),
        fps=config.get("fps"),
        debug_enabled=bool(config.get("debug_enabled", False)),
    )
    return keypoints_payload(
        keypoints=result.get("keypoints") or {},
        fps=float(result.get("fps") or 0.0),
        metadata=dict(result.get("metadata") or {}),
    )


if __name__ == "__main__":
    run_cli("extract_keypoints", extract_keypoints)
