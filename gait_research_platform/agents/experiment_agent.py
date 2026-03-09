from __future__ import annotations

from pathlib import Path
from typing import Any

from gait_research_platform.agents.experiment_planner import ExperimentPlanner
from gait_research_platform.core.config_loader import merge_config, save_config
from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.pipeline.run_experiment import run_experiment


class ExperimentAgent:
    def __init__(self, base_config: dict[str, Any], planner: ExperimentPlanner | None = None) -> None:
        self.base_config = merge_config(base_config)
        self.data_manager = DataManager(self.base_config)
        self.planner = planner or ExperimentPlanner(self.base_config)

    def plan(self, goal: str, use_llm: bool = False, num_candidates: int = 1) -> list[dict[str, Any]]:
        return self.planner.plan(goal=goal, use_llm=use_llm, num_candidates=num_candidates)

    def save_plan(self, config: dict[str, Any], output_path: str | Path) -> Path:
        path = Path(output_path)
        save_config(config, path)
        return path

    def save_generated_plan(self, config: dict[str, Any], name: str | None = None) -> Path:
        experiment_id = config.get("experiment", {}).get("experiment_id", "auto")
        slug = name or f"generated_{experiment_id if experiment_id != 'auto' else 'experiment'}"
        path = Path(self.base_config["data"]["root_dir"]) / "gait_research_platform" / "configs" / "experiments" / "generated" / f"{slug}.yaml"
        save_config(config, path)
        return path

    def run(self, config_or_path: dict[str, Any] | str | Path) -> dict[str, Any]:
        if isinstance(config_or_path, (str, Path)):
            from gait_research_platform.core.config_loader import load_config

            config = load_config(config_or_path)
        else:
            config = merge_config(config_or_path)
        return run_experiment(config)

    def review(self, results_manifest_entry: dict[str, Any]) -> dict[str, Any]:
        metrics = results_manifest_entry.get("metrics", {})
        status = results_manifest_entry.get("status", "unknown")
        recommendation = "Inspect embeddings and try a larger embedding dimension."
        if status != "success":
            recommendation = "Resolve the failed run before exploring new signal combinations."
        elif metrics.get("final_loss", 1.0) < 0.2:
            recommendation = "Training looks stable. Add periodicity or clustering analysis next."
        return {
            "status": status,
            "experiment_id": results_manifest_entry.get("experiment_id"),
            "recommendation": recommendation,
            "metrics": metrics,
        }

    def latest_reviews(self, limit: int = 3) -> list[dict[str, Any]]:
        return [self.review(entry) for entry in self.data_manager.read_manifest(limit=limit)]
