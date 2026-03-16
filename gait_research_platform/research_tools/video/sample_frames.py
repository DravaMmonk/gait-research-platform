from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.common.paths import ensure_parent_dir, read_json, require_file, write_json


def sample_frames(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    video_path = require_file(input_path)
    config = dict(config or {})
    decoded_path = config.get("decoded_video_path")
    fps = float((read_json(decoded_path)["video"]["fps"]) if decoded_path else config.get("fps", 1.0))
    sample_every = max(1.0, float(config.get("sample_every_seconds", 1.0)))
    output_dir = ensure_parent_dir(config.get("frames_dir") or Path(output_path).with_suffix("").as_posix())
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / "frame_%04d.jpg"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={max(fps / max(1.0, fps * sample_every), 1.0 / sample_every):.6f}",
        str(output_pattern),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is required for sample_frames but is not installed.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg failed while sampling frames: {exc.stderr.strip()}") from exc
    frames = sorted(str(path) for path in output_dir.glob("frame_*.jpg"))
    payload = {
        "schema_version": "v1",
        "frames": frames,
        "summary": {
            "tool": "sample_frames",
            "sample_every_seconds": sample_every,
            "frame_count": len(frames),
        },
    }
    write_json(output_path, payload)
    return {"tool": "sample_frames", "output_path": output_path, "frame_count": len(frames)}


if __name__ == "__main__":
    run_cli("sample_frames", sample_frames)
