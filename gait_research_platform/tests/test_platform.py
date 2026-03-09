from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from gait_research_platform.agents.experiment_agent import ExperimentAgent
from gait_research_platform.agents.experiment_planner import ExperimentPlanner
from gait_research_platform.core.config_loader import load_config, merge_config
from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.data.sample_pose_dataset import generate_sample_pose_dataset
from gait_research_platform.pipeline.run_experiment import run_experiment
from gait_research_platform.signals.velocity_signal import VelocitySignal


def base_config(tmp_path: Path) -> dict:
    return merge_config(
        {
            "data": {
                "root_dir": str(tmp_path),
                "videos_dir": "videos",
                "poses_dir": "poses",
                "signals_dir": "signals",
                "embeddings_dir": "embeddings",
                "results_dir": "results",
                "manifest_path": "results/manifest.jsonl",
            },
            "signals": [{"name": "velocity_signal", "enabled": True, "params": {"normalize": True}}],
            "representation": {
                "model": "temporal_embedding",
                "params": {"input_dim": "auto", "embedding_dim": 16, "channels": [16, 32], "kernel_size": 3},
            },
            "training": {"batch_size": 2, "epochs": 1, "learning_rate": 1e-3, "temperature": 0.1, "num_workers": 0},
            "analysis": [{"name": "embedding_visualization", "params": {"method": "tsne"}}],
            "agent": {"enabled": False, "provider": "openai_compatible", "model": "test-model"},
        }
    )


class MockLLM:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def generate(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2) -> str:
        del prompt, system_prompt, temperature
        return self.payload


def write_config(path: Path, config: dict) -> None:
    import yaml

    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def test_load_config_rejects_missing_signals(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.yaml"
    config_path.write_text("signals: []\nrepresentation:\n  model: temporal_embedding\n", encoding="utf-8")
    try:
        load_config(config_path)
    except ValueError as exc:
        assert "at least one signal" in str(exc)
    else:
        raise AssertionError("load_config should reject config without signals")


def test_data_manager_ensure_pose_requires_input(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    manager = DataManager(config)
    try:
        manager.ensure_pose("missing_video")
    except FileNotFoundError as exc:
        assert "Pose file missing" in str(exc)
    else:
        raise AssertionError("ensure_pose should fail without pose parquet or extractor")


def test_velocity_signal_shape() -> None:
    pose = pd.DataFrame(
        {
            "frame_index": [0, 1, 2],
            "hip_x": [0.0, 1.0, 3.0],
            "hip_y": [0.0, 2.0, 4.0],
        }
    )
    signal = VelocitySignal(normalize=False)
    features = signal.build("vid", pose)
    assert features.shape == (3, 2)


def test_planner_rejects_unknown_allowed_modules_and_clamps_limits(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    planner = ExperimentPlanner(config)
    try:
        planner.plan(goal="test", allowed_signals=["unknown_signal"], use_llm=False)
    except ValueError as exc:
        assert "Unknown allowed signals" in str(exc)
    else:
        raise AssertionError("Planner should reject unknown allowed modules")

    llm_payload = json.dumps(
        {
            "signals": [{"name": "velocity_signal", "enabled": True, "params": {"normalize": True}}],
            "representation": {"model": "temporal_embedding", "params": {"input_dim": "auto", "embedding_dim": 999}},
            "training": {"epochs": 999},
        }
    )
    planner = ExperimentPlanner(config, llm_client=MockLLM(llm_payload))
    plan = planner.plan(
        goal="test",
        allowed_signals=["velocity_signal"],
        allowed_representations=["temporal_embedding"],
        use_llm=True,
    )[0]
    assert plan["training"]["epochs"] == 50
    assert plan["representation"]["params"]["embedding_dim"] == 128


def test_planner_handles_malformed_llm_output(tmp_path: Path) -> None:
    planner = ExperimentPlanner(base_config(tmp_path), llm_client=MockLLM("not-json"))
    try:
        planner.plan(
            goal="test",
            allowed_signals=["velocity_signal"],
            allowed_representations=["temporal_embedding"],
            use_llm=True,
        )
    except ValueError as exc:
        assert "parsed" in str(exc).lower()
    else:
        raise AssertionError("Planner should reject malformed LLM output")


def test_run_experiment_success_persists_artifacts(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    generate_sample_pose_dataset(tmp_path / "poses", num_videos=4, num_frames=32)

    result = run_experiment(config)
    result_dir = Path(result["result_dir"])
    assert result["status"] == "success"
    assert result["error"] is None
    assert (result_dir / "config.yaml").exists()
    assert (result_dir / "metrics.json").exists()
    assert (result_dir / "summary.json").exists()
    assert (result_dir / "error.json").exists()
    assert (result_dir / "logs.txt").exists()
    assert (result_dir / "plots" / "embedding_visualization.png").exists()

    manifest = (tmp_path / "results" / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    latest = json.loads(manifest[-1])
    assert latest["status"] == "success"
    assert latest["error"] is None


def test_run_experiment_failure_returns_structured_error(tmp_path: Path) -> None:
    result = run_experiment(base_config(tmp_path))
    result_dir = Path(result["result_dir"])
    assert result["status"] == "failed"
    assert result["metrics"] is None
    assert result["error"]["stage"] == "signal"
    assert (result_dir / "error.json").exists()

    manifest = (tmp_path / "results" / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    latest = json.loads(manifest[-1])
    assert latest["status"] == "failed"
    assert latest["error"]["type"] in {"FileNotFoundError", "ValueError"}


def test_agent_execution_gate_and_rule_review(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    agent = ExperimentAgent(config)
    plan = agent.plan(
        goal="test",
        allowed_signals=["velocity_signal"],
        allowed_representations=["temporal_embedding"],
        use_llm=False,
    )[0]
    run_request = agent.request_run(plan)
    blocked = agent.run(run_request, approved=False)
    assert blocked["status"] == "failed"
    assert blocked["error"]["type"] == "PermissionError"

    review = agent.review(blocked)
    assert review["review_mode"] == "rules"
    assert "approve" in review["recommendation"].lower()


def test_agent_llm_review_success_and_failure(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    generate_sample_pose_dataset(tmp_path / "poses", num_videos=3, num_frames=24)
    llm = MockLLM(json.dumps({"analysis": "Stable embedding behavior.", "recommendation": "Increase embedding_dim to 32."}))
    agent = ExperimentAgent(config, llm_client=llm)

    result = run_experiment(config)
    review = agent.review(result)
    assert review["review_mode"] == "llm"
    assert "Stable" in review["analysis"]

    failed = run_experiment(base_config(tmp_path / "missing"))
    failed_agent = ExperimentAgent(base_config(tmp_path / "missing"), llm_client=llm)
    failed_review = failed_agent.review(failed)
    assert failed_review["review_mode"] == "llm"
    assert "Increase" in failed_review["recommendation"]


def test_agent_cli_smoke(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    generate_sample_pose_dataset(tmp_path / "poses", num_videos=3, num_frames=24)
    config_path = tmp_path / "config.yaml"
    write_config(config_path, config)

    plan_cmd = [
        sys.executable,
        "-m",
        "gait_research_platform.agents.agent_loop",
        "--base-config",
        str(config_path),
        "plan",
        "--goal",
        "cli smoke",
    ]
    plan_output = subprocess.run(plan_cmd, check=True, capture_output=True, text=True)
    planned = json.loads(plan_output.stdout)
    assert isinstance(planned, list)

    run_cmd = [
        sys.executable,
        "-m",
        "gait_research_platform.agents.agent_loop",
        "--base-config",
        str(config_path),
        "run",
        "--config",
        str(config_path),
        "--approve",
    ]
    run_output = subprocess.run(run_cmd, check=True, capture_output=True, text=True)
    run_result = json.loads(run_output.stdout)
    assert run_result["status"] == "success"

    review_cmd = [
        sys.executable,
        "-m",
        "gait_research_platform.agents.agent_loop",
        "--base-config",
        str(config_path),
        "review",
        "--experiment-id",
        run_result["experiment_id"],
    ]
    review_output = subprocess.run(review_cmd, check=True, capture_output=True, text=True)
    reviewed = json.loads(review_output.stdout)
    assert reviewed["status"] == "success"
