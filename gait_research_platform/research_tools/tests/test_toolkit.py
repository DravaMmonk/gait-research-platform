from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from research_tools.gait.compute_gait_metrics import compute_gait_metrics
from research_tools.gait.compute_stride import compute_stride
from research_tools.gait.detect_direction import detect_direction
from research_tools.gait.segment_sections import segment_sections
from research_tools.pose.extract_keypoints import extract_keypoints
from research_tools.reports.generate_report import generate_report
from research_tools.symbolic.manifest_visualizer import summarize_manifest, visualize_manifest
from research_tools.video.decode_video import decode_video


def test_decode_video_writes_metadata(tmp_path, monkeypatch):
    video_path = tmp_path / "input.mp4"
    output_path = tmp_path / "decoded.json"
    video_path.write_bytes(b"video")

    monkeypatch.setattr(
        "research_tools.video.decode_video._probe_video",
        lambda path: {
            "fps": 30.0,
            "frame_count": 42,
            "duration_seconds": 1.4,
            "width": 640,
            "height": 480,
            "codec": "h264",
        },
    )

    result = decode_video(str(video_path), str(output_path))
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert result["video"]["frame_count"] == 42
    assert payload["video"]["codec"] == "h264"


def test_extract_keypoints_writes_mock_payload(tmp_path):
    video_path = tmp_path / "input.mp4"
    output_path = tmp_path / "keypoints.json"
    video_path.write_bytes(b"video")

    result = extract_keypoints(
        str(video_path),
        str(output_path),
        {"mock_payload": build_keypoints_payload()},
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert "left_front_paw" in payload["keypoints"]
    assert result["fps"] == 30.0


def test_gait_pipeline_happy_path(tmp_path):
    keypoints_path = tmp_path / "keypoints.json"
    directions_path = tmp_path / "directions.json"
    sections_path = tmp_path / "sections.json"
    stride_path = tmp_path / "stride.json"
    metrics_path = tmp_path / "metrics.json"
    report_path = tmp_path / "report.json"

    keypoints_path.write_text(json.dumps(build_keypoints_payload()), encoding="utf-8")

    detect_direction(str(keypoints_path), str(directions_path))
    segment_sections(str(directions_path), str(sections_path), {"min_duration_seconds": 0.2})
    compute_stride(str(keypoints_path), str(stride_path), {"sections_path": str(sections_path)})
    compute_gait_metrics(
        str(keypoints_path),
        str(metrics_path),
        {"sections_path": str(sections_path), "stride_path": str(stride_path)},
    )
    generate_report(
        str(metrics_path),
        str(report_path),
        {"sections_path": str(sections_path), "stride_path": str(stride_path)},
    )

    directions = json.loads(directions_path.read_text(encoding="utf-8"))
    sections = json.loads(sections_path.read_text(encoding="utf-8"))
    stride = json.loads(stride_path.read_text(encoding="utf-8"))
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert directions["summary"]["frame_count"] > 0
    assert sections["summary"]["section_count"] >= 1
    assert stride["summary"]["section_count"] >= 1
    assert "symmetry" in metrics["metrics"]
    assert report["report"]["recommendations"]


def test_detect_direction_cli(tmp_path):
    keypoints_path = tmp_path / "keypoints.json"
    output_path = tmp_path / "directions.json"
    keypoints_path.write_text(json.dumps(build_keypoints_payload()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "research_tools/gait/detect_direction.py",
            "--input",
            str(keypoints_path),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )

    assert "\"tool\": \"detect_direction\"" in completed.stdout
    assert output_path.exists()


def test_missing_file_errors(tmp_path):
    missing = tmp_path / "missing.json"
    output = tmp_path / "out.json"
    try:
        detect_direction(str(missing), str(output))
    except FileNotFoundError as exc:
        assert "Required input file not found" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_visualize_manifest_writes_review_artifacts(tmp_path):
    manifest_path = tmp_path / "manifest.yaml"
    report_path = tmp_path / "manifest_review.json"
    manifest_path.write_text(
        """
experiment:
  experiment_id: test_manifest
medical_constraints:
  allowed_signals: [stride_length, left_stride, right_stride]
  allowed_operators: [add, sub, abs]
  max_formula_depth: 4
research_definition:
  research_question: "Can asymmetry predict discomfort?"
  target_variable: pain_score
  candidate_variables: [stride_length, left_stride, right_stride]
signals:
  - name: stride_length
    type: gait
  - name: left_stride
    type: gait
  - name: right_stride
    type: gait
operator_registry:
  add:
    arity: 2
  sub:
    arity: 2
  abs:
    arity: 1
formula_constraints:
  max_depth: 4
  max_nodes: 12
search_config:
  engine: pysr
validation:
  cross_validation: 5
""".strip(),
        encoding="utf-8",
    )

    result = visualize_manifest(str(manifest_path), str(report_path))
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert result["tool"] == "visualize_manifest"
    assert payload["summary"]["experiment_id"] == "test_manifest"
    assert report_path.with_suffix(".html").exists()


def test_summarize_manifest_flags_schema_mismatches():
    payload = summarize_manifest(
        {
            "experiment": {"experiment_id": "test_manifest"},
            "medical_constraints": {
                "allowed_signals": ["stride_length"],
                "allowed_operators": ["add", "abs"],
                "max_formula_depth": 3,
            },
            "research_definition": {
                "research_question": "Can asymmetry predict discomfort?",
                "target_variable": "pain_score",
                "candidate_variables": ["stride_length", "right_stride"],
            },
            "signals": [{"name": "stride_length", "type": "gait"}],
            "operator_registry": {"add": {"arity": 2}},
            "formula_constraints": {"max_depth": 4},
            "search_config": {"engine": "pysr"},
            "validation": {"cross_validation": 2},
        }
    )

    assert payload["warnings"]
    assert any("candidate_variables" in item for item in payload["warnings"])
    assert any("cross_validation" in item for item in payload["warnings"])


def test_toolkit_avoids_platform_runtime_imports():
    repo_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [
            "rg",
            "-n",
            r"app\\.services|workers\\.runtime|workers\\.capabilities\\..*handler|app\\.clients",
            "research_tools",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1, completed.stdout


def build_keypoints_payload() -> dict[str, object]:
    frame_count = 48
    fps = 30.0
    keypoints: dict[str, list[dict[str, float]]] = {}

    def add_part(name: str, x_fn, y_fn, confidence: float = 0.95):
        keypoints[name] = [
            {"x": round(float(x_fn(frame)), 4), "y": round(float(y_fn(frame)), 4), "c": confidence}
            for frame in range(frame_count)
        ]

    for frame_name, base_y in {
        "nose": 40.0,
        "head": 45.0,
        "upper_spine": 60.0,
        "mid_spine": 65.0,
        "lower_spine": 70.0,
        "pelvis": 72.0,
        "tail_base": 74.0,
    }.items():
        add_part(frame_name, lambda f, shift=base_y: 100.0 + f * 2.0 + (shift - 40.0) * 0.2, lambda _f, y=base_y: y)

    side_offsets = {"left": -12.0, "right": 12.0}
    for side, side_offset in side_offsets.items():
        add_part(f"{side}_shoulder", lambda f, o=side_offset: 120.0 + f * 2.0 + o, lambda _f: 62.0)
        add_part(f"{side}_elbow", lambda f, o=side_offset: 132.0 + f * 2.0 + o, lambda f: 88.0 + 1.2 * __import__("math").sin(f / 4.0))
        add_part(f"{side}_wrist", lambda f, o=side_offset: 144.0 + f * 2.0 + o, lambda f: 112.0 + 2.0 * __import__("math").sin(f / 4.0))
        add_part(
            f"{side}_front_paw",
            lambda f, o=side_offset: 156.0 + f * 2.0 + o + 6.0 * __import__("math").sin(f / 3.0 + (0 if side == "left" else 1.2)),
            lambda f: 132.0 + 6.0 * __import__("math").sin(f / 3.0 + (0 if side == "left" else 1.2)),
        )
        add_part(f"{side}_hip", lambda f, o=side_offset: 186.0 + f * 2.0 + o, lambda _f: 74.0)
        add_part(f"{side}_knee", lambda f, o=side_offset: 196.0 + f * 2.0 + o, lambda f: 100.0 + 1.5 * __import__("math").sin(f / 4.0))
        add_part(f"{side}_ankle", lambda f, o=side_offset: 206.0 + f * 2.0 + o, lambda f: 122.0 + 2.5 * __import__("math").sin(f / 4.0))
        add_part(
            f"{side}_hind_paw",
            lambda f, o=side_offset: 216.0 + f * 2.0 + o + 6.5 * __import__("math").sin(f / 3.2 + (1.0 if side == "left" else 2.0)),
            lambda f: 138.0 + 7.0 * __import__("math").sin(f / 3.2 + (1.0 if side == "left" else 2.0)),
        )

    return {
        "schema_version": "v1",
        "fps": fps,
        "metadata": {"source": "synthetic-test"},
        "keypoints": keypoints,
    }
