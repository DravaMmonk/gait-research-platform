from __future__ import annotations

from copy import deepcopy
from typing import Any

from gait_research_platform.agents.llm_client import LLMClient, OpenAICompatibleClient, config_from_llm_output
from gait_research_platform.core.config_loader import merge_config
from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.core.registry import registry


class ExperimentPlanner:
    def __init__(self, config: dict[str, Any], llm_client: LLMClient | None = None) -> None:
        self.config = config
        self.llm_client = llm_client
        self.data_manager = DataManager(config)

    def plan(self, goal: str, use_llm: bool = False, num_candidates: int = 1) -> list[dict[str, Any]]:
        history = self.data_manager.read_manifest(limit=5)
        if use_llm:
            client = self.llm_client or OpenAICompatibleClient(default_model=self.config["agent"]["model"])
            return self._plan_with_llm(goal, history, client, num_candidates=num_candidates)
        return self._plan_with_template(goal, history, num_candidates=num_candidates)

    def _plan_with_template(
        self,
        goal: str,
        history: list[dict[str, Any]],
        num_candidates: int = 1,
    ) -> list[dict[str, Any]]:
        del history
        configs: list[dict[str, Any]] = []
        for index in range(num_candidates):
            planned = deepcopy(self.config)
            planned["agent"]["enabled"] = True
            planned["experiment"]["experiment_id"] = "auto"
            planned["experiment"]["goal"] = goal
            planned["representation"]["params"]["embedding_dim"] = 64 + index * 32
            planned["training"]["epochs"] = max(1, int(planned["training"].get("epochs", 10)))
            configs.append(merge_config(planned))
        return configs

    def _plan_with_llm(
        self,
        goal: str,
        history: list[dict[str, Any]],
        client: LLMClient,
        num_candidates: int = 1,
    ) -> list[dict[str, Any]]:
        prompt = {
            "goal": goal,
            "available_signals": registry.list_signals(),
            "available_representations": registry.list_representations(),
            "available_experiments": registry.list_experiments(),
            "available_analysis": registry.list_analysis_tasks(),
            "recent_experiments": history,
            "base_config": self.config,
            "instructions": (
                "Return a JSON array of experiment configs. "
                f"Generate exactly {num_candidates} config object(s). "
                "Only use registered component names. Keep output as raw JSON."
            ),
        }
        messages = [
            {"role": "system", "content": "You are a research planning assistant for gait representation experiments."},
            {"role": "user", "content": str(prompt)},
        ]
        response = client.generate_text(messages=messages, model=self.config["agent"]["model"])
        parsed = config_from_llm_output(response)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            raise ValueError("Planner expected a JSON object or array of objects.")
        return [merge_config(item) for item in parsed]
