from __future__ import annotations

import json
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
        }
    )


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


def test_run_experiment_and_manifest(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    generate_sample_pose_dataset(tmp_path / "poses", num_videos=4, num_frames=32)

    result = run_experiment(config)
    result_dir = Path(result["result_dir"])
    assert result_dir.exists()
    assert (result_dir / "metrics.json").exists()
    assert (result_dir / "summary.json").exists()
    assert (result_dir / "plots" / "embedding_visualization.png").exists()

    manifest = (tmp_path / "results" / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    assert manifest
    latest = json.loads(manifest[-1])
    assert latest["status"] == "success"


class MockLLM:
    def generate_text(self, messages, model=None, temperature=0.2):  # noqa: D401
        del messages, model, temperature
        return json.dumps(
            {
                "signals": [{"name": "velocity_signal", "enabled": True, "params": {"normalize": True}}],
                "representation": {"model": "temporal_embedding", "params": {"input_dim": "auto", "embedding_dim": 32}},
            }
        )


def test_agent_planner_template_and_llm(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    planner = ExperimentPlanner(config, llm_client=MockLLM())
    template_plan = planner.plan(goal="test", use_llm=False, num_candidates=2)
    llm_plan = planner.plan(goal="test", use_llm=True, num_candidates=1)
    assert len(template_plan) == 2
    assert llm_plan[0]["representation"]["params"]["embedding_dim"] == 32


def test_agent_review(tmp_path: Path) -> None:
    config = base_config(tmp_path)
    agent = ExperimentAgent(config)
    review = agent.review({"experiment_id": "exp1", "status": "success", "metrics": {"final_loss": 0.1}})
    assert "periodicity" in review["recommendation"].lower()
