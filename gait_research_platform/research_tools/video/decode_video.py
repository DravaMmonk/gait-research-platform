from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.common.paths import require_file, write_json


def decode_video(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    del config
    video_path = require_file(input_path)
    metadata = _probe_video(video_path)
    payload = {
        "schema_version": "v1",
        "video": {
            "path": str(video_path),
            "fps": metadata["fps"],
            "frame_count": metadata["frame_count"],
            "duration_seconds": metadata["duration_seconds"],
            "width": metadata["width"],
            "height": metadata["height"],
            "codec": metadata["codec"],
        },
        "summary": {"tool": "decode_video", "status": "ok"},
    }
    write_json(output_path, payload)
    return {"tool": "decode_video", "output_path": output_path, "video": payload["video"]}


def _probe_video(video_path: Path) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,avg_frame_rate,nb_frames,duration",
        "-of",
        "json",
        str(video_path),
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("ffprobe is required for decode_video but is not installed.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffprobe failed for {video_path}: {exc.stderr.strip()}") from exc
    raw = json.loads(completed.stdout or "{}")
    stream = ((raw.get("streams") or [{}])[0]) if isinstance(raw, dict) else {}
    fps = _parse_frame_rate(stream.get("avg_frame_rate"))
    duration = float(stream.get("duration") or 0.0)
    frame_count = int(float(stream.get("nb_frames") or 0) or round(duration * fps))
    return {
        "fps": fps,
        "frame_count": frame_count,
        "duration_seconds": duration,
        "width": int(stream.get("width") or 0),
        "height": int(stream.get("height") or 0),
        "codec": stream.get("codec_name"),
    }


def _parse_frame_rate(value: Any) -> float:
    text = str(value or "0")
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        denom = float(denominator or 1)
        return float(numerator or 0) / denom if denom else 0.0
    return float(text or 0)


if __name__ == "__main__":
    run_cli("decode_video", decode_video)
