from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from gait_research_platform.agents.experiment_planner import ExperimentPlanner
from gait_research_platform.agents.llm_client import LLMClient, config_from_llm_output
from gait_research_platform.core.config_loader import load_config, merge_config, save_config
from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.pipeline.run_experiment import run_experiment


class ExperimentAgent:
    def __init__(
        self,
        base_config: dict[str, Any],
        planner: ExperimentPlanner | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.base_config = merge_config(base_config)
        self.data_manager = DataManager(self.base_config)
        self.llm_client = llm_client
        self.planner = planner or ExperimentPlanner(self.base_config, llm_client=llm_client)

    def plan(
        self,
        goal: str,
        allowed_signals: list[str] | None = None,
        allowed_representations: list[str] | None = None,
        use_llm: bool = True,
        num_candidates: int = 1,
    ) -> list[dict[str, Any]]:
        return self.planner.plan(
            goal=goal,
            allowed_signals=allowed_signals,
            allowed_representations=allowed_representations,
            use_llm=use_llm,
            num_candidates=num_candidates,
        )

    def save_plan(self, config: dict[str, Any], output_path: str | Path) -> Path:
        path = Path(output_path)
        save_config(config, path)
        return path

    def save_generated_plan(self, config: dict[str, Any], name: str | None = None) -> Path:
        experiment_id = config.get("experiment", {}).get("experiment_id", "auto")
        slug = name or f"generated_{experiment_id if experiment_id != 'auto' else 'experiment'}"
        path = (
            Path(self.base_config["data"]["root_dir"])
            / "gait_research_platform"
            / "configs"
            / "experiments"
            / "generated"
            / f"{slug}.yaml"
        )
        save_config(config, path)
        return path

    def request_run(self, config: dict[str, Any] | str | Path) -> dict[str, Any]:
        normalized = self._normalize_config_input(config)
        return {
            "approval_token": secrets.token_urlsafe(16),
            "config": normalized,
            "summary": {
                "experiment_name": normalized["experiment"]["name"],
                "signals": [item["name"] for item in normalized["signals"] if item.get("enabled", True)],
                "representation": normalized["representation"]["model"],
                "epochs": normalized["training"]["epochs"],
                "embedding_dim": normalized["representation"].get("params", {}).get("embedding_dim"),
            },
        }

    def run(self, run_request: dict[str, Any], approved: bool = False) -> dict[str, Any]:
        if not approved:
            return {
                "experiment_id": run_request.get("config", {}).get("experiment", {}).get("experiment_id", "pending"),
                "status": "failed",
                "result_dir": None,
                "metrics": None,
                "summary": None,
                "error": {
                    "type": "PermissionError",
                    "message": "Experiment run requires explicit approval.",
                    "traceback": None,
                    "stage": "config",
                },
            }
        config = self._normalize_config_input(run_request["config"])
        return run_experiment(config)

    def review(self, experiment_result: dict[str, Any]) -> dict[str, Any]:
        experiment_id = experiment_result["experiment_id"]
        result_dir_value = experiment_result.get("result_dir")
        result_dir = Path(result_dir_value) if result_dir_value else self.data_manager.result_dir(experiment_id)
        metrics = experiment_result.get("metrics")
        summary = experiment_result.get("summary") or self.data_manager.load_summary(result_dir)
        error = experiment_result.get("error") or self.data_manager.load_error(result_dir)
        recent_experiments = self.data_manager.read_manifest(limit=5)

        if self.llm_client is not None:
            try:
                return self._review_with_llm(
                    experiment_id=experiment_id,
                    status=experiment_result["status"],
                    metrics=metrics,
                    summary=summary,
                    error=error,
                    recent_experiments=recent_experiments,
                )
            except Exception:
                pass
        return self._review_with_rules(
            experiment_id=experiment_id,
            status=experiment_result["status"],
            metrics=metrics,
            error=error,
            recent_experiments=recent_experiments,
        )

    def latest_reviews(self, limit: int = 3) -> list[dict[str, Any]]:
        results = []
        for entry in self.data_manager.read_manifest(limit=limit):
            results.append(self.review(entry))
        return results

    def _normalize_config_input(self, config_or_path: dict[str, Any] | str | Path) -> dict[str, Any]:
        if isinstance(config_or_path, (str, Path)):
            return load_config(config_or_path)
        return merge_config(config_or_path)

    def _review_with_llm(
        self,
        experiment_id: str,
        status: str,
        metrics: dict[str, Any] | None,
        summary: dict[str, Any] | None,
        error: dict[str, Any] | None,
        recent_experiments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        prompt = json.dumps(
            {
                "experiment_id": experiment_id,
                "status": status,
                "metrics": metrics,
                "summary": summary,
                "error": error,
                "recent_experiments": recent_experiments,
                "instructions": {
                    "analysis": "Explain the outcome briefly.",
                    "recommendation": "Suggest the next config-safe experiment step only.",
                    "forbidden": ["source code edits", "git operations", "data preprocessing"],
                },
            },
            indent=2,
        )
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=(
                "You are a gait research review agent. "
                "Return JSON with keys 'analysis' and 'recommendation'. "
                "Recommendations must be config-safe and experiment-focused."
            ),
        )
        parsed = config_from_llm_output(response)
        return {
            "experiment_id": experiment_id,
            "status": status,
            "analysis": parsed["analysis"],
            "recommendation": parsed["recommendation"],
            "based_on": {
                "metrics": metrics,
                "error": error,
                "recent_experiments": recent_experiments,
            },
            "review_mode": "llm",
        }

    def _review_with_rules(
        self,
        experiment_id: str,
        status: str,
        metrics: dict[str, Any] | None,
        error: dict[str, Any] | None,
        recent_experiments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if status == "failed":
            stage = (error or {}).get("stage", "unknown")
            message = (error or {}).get("message", "")
            if stage == "signal":
                analysis = "The experiment failed while building signals."
                recommendation = "Check pose availability and switch to a pose-compatible signal configuration."
            elif stage == "training":
                analysis = "The experiment failed during model training."
                recommendation = "Reduce training complexity or inspect the generated signal dimensions before rerunning."
            elif "approval" in message.lower():
                analysis = "The run was blocked by the execution gate."
                recommendation = "Approve the run request explicitly before execution."
            else:
                analysis = "The experiment failed before completion."
                recommendation = "Use the recorded error stage and message to adjust the next config conservatively."
        else:
            final_loss = float((metrics or {}).get("final_loss", 1.0))
            embedding_dim = (metrics or {}).get("embedding_dim")
            if final_loss < 0.2:
                analysis = "The training signal looks stable for this configuration."
                recommendation = "Keep the current signal set and add a new analysis task such as periodicity or clustering."
            elif embedding_dim and int(embedding_dim) < 128:
                analysis = "The experiment completed but still has room for representation tuning."
                recommendation = "Increase the embedding dimension within the MVP limit and compare against the latest run."
            else:
                analysis = "The experiment completed successfully."
                recommendation = "Try a neighboring configuration change rather than widening the search space."

        return {
            "experiment_id": experiment_id,
            "status": status,
            "analysis": analysis,
            "recommendation": recommendation,
            "based_on": {
                "metrics": metrics,
                "error": error,
                "recent_experiments": recent_experiments,
            },
            "review_mode": "rules",
        }
