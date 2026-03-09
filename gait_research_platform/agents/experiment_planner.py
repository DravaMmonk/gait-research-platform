from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from gait_research_platform.agents.llm_client import LLMClient, OpenAICompatibleClient, config_from_llm_output
from gait_research_platform.core.config_loader import merge_config
from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.core.registry import registry


class ExperimentPlanner:
    def __init__(self, config: dict[str, Any], llm_client: LLMClient | None = None) -> None:
        self.config = merge_config(config)
        self.llm_client = llm_client
        self.data_manager = DataManager(self.config)

    def plan(
        self,
        goal: str,
        allowed_signals: list[str] | None = None,
        allowed_representations: list[str] | None = None,
        recent_experiments: list[dict[str, Any]] | None = None,
        use_llm: bool = True,
        num_candidates: int = 1,
    ) -> list[dict[str, Any]]:
        history = recent_experiments if recent_experiments is not None else self.data_manager.read_manifest(limit=5)
        allowed_signals = allowed_signals or registry.list_signals()
        allowed_representations = allowed_representations or registry.list_representations()

        self._validate_allowed_modules(allowed_signals, allowed_representations)
        if use_llm:
            client = self.llm_client or OpenAICompatibleClient(default_model=self.config["agent"]["model"])
            return self._plan_with_llm(goal, allowed_signals, allowed_representations, history, client, num_candidates)
        return self._plan_with_template(goal, allowed_signals, allowed_representations, history, num_candidates)

    def _validate_allowed_modules(self, allowed_signals: list[str], allowed_representations: list[str]) -> None:
        known_signals = set(registry.list_signals())
        known_representations = set(registry.list_representations())
        unknown_signals = sorted(set(allowed_signals) - known_signals)
        unknown_representations = sorted(set(allowed_representations) - known_representations)
        if unknown_signals:
            raise ValueError(f"Unknown allowed signals: {unknown_signals}")
        if unknown_representations:
            raise ValueError(f"Unknown allowed representations: {unknown_representations}")

    def _plan_with_template(
        self,
        goal: str,
        allowed_signals: list[str],
        allowed_representations: list[str],
        history: list[dict[str, Any]],
        num_candidates: int,
    ) -> list[dict[str, Any]]:
        del history
        configs: list[dict[str, Any]] = []
        default_signal = "velocity_signal" if "velocity_signal" in allowed_signals else allowed_signals[0]
        default_representation = (
            "temporal_embedding" if "temporal_embedding" in allowed_representations else allowed_representations[0]
        )
        for index in range(num_candidates):
            planned = deepcopy(self.config)
            planned["agent"]["enabled"] = True
            planned["experiment"]["experiment_id"] = "auto"
            planned["experiment"]["goal"] = goal
            planned["signals"] = [{"name": default_signal, "enabled": True, "params": {"normalize": True}}]
            planned["representation"]["model"] = default_representation
            planned["representation"]["params"]["embedding_dim"] = min(128, 64 + index * 32)
            planned["training"]["epochs"] = min(50, max(1, int(planned["training"].get("epochs", 10))))
            configs.append(self._finalize_plan(planned, allowed_signals, allowed_representations))
        return configs

    def _plan_with_llm(
        self,
        goal: str,
        allowed_signals: list[str],
        allowed_representations: list[str],
        history: list[dict[str, Any]],
        client: LLMClient,
        num_candidates: int,
    ) -> list[dict[str, Any]]:
        prompt = json.dumps(
            {
                "goal": goal,
                "allowed_signals": allowed_signals,
                "allowed_representations": allowed_representations,
                "available_experiments": registry.list_experiments(),
                "available_analysis": registry.list_analysis_tasks(),
                "recent_experiments": history,
                "base_config": self.config,
                "constraints": {
                    "epochs_max": 50,
                    "embedding_dim_max": 128,
                    "no_new_modules": True,
                    "output_format": "Return JSON only. Use a single object or an array of objects.",
                },
            },
            indent=2,
        )
        response = client.generate(
            prompt=prompt,
            system_prompt=(
                "You are a gait research experiment planner. "
                "Return JSON configs using only allowed modules and config-safe changes."
            ),
        )
        parsed = config_from_llm_output(response)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            raise ValueError("Planner expected a JSON object or JSON array of config objects.")
        plans = []
        for item in parsed[:num_candidates]:
            plans.append(self._finalize_plan(item, allowed_signals, allowed_representations))
        if not plans:
            raise ValueError("Planner did not produce any candidate configs.")
        return plans

    def _finalize_plan(
        self,
        candidate: dict[str, Any],
        allowed_signals: list[str],
        allowed_representations: list[str],
    ) -> dict[str, Any]:
        cleaned = self._strip_unsupported_fields(candidate)
        merged = merge_config(cleaned)
        self._validate_plan(merged, allowed_signals, allowed_representations)
        self._apply_limits(merged)
        return merged

    def _strip_unsupported_fields(self, candidate: dict[str, Any]) -> dict[str, Any]:
        allowed_root_keys = {"experiment", "data", "signals", "representation", "training", "analysis", "agent"}
        return {key: value for key, value in candidate.items() if key in allowed_root_keys}

    def _validate_plan(
        self,
        config: dict[str, Any],
        allowed_signals: list[str],
        allowed_representations: list[str],
    ) -> None:
        configured_signals = [signal["name"] for signal in config["signals"] if signal.get("enabled", True)]
        unknown_signals = sorted(set(configured_signals) - set(allowed_signals))
        if unknown_signals:
            raise ValueError(f"Planner selected disallowed signals: {unknown_signals}")

        representation_name = config["representation"]["model"]
        if representation_name not in allowed_representations:
            raise ValueError(f"Planner selected disallowed representation: {representation_name}")

        if config["experiment"]["name"] not in registry.list_experiments():
            raise ValueError(f"Planner selected unknown experiment: {config['experiment']['name']}")

        analysis_names = [item["name"] for item in config.get("analysis", [])]
        unknown_analysis = sorted(set(analysis_names) - set(registry.list_analysis_tasks()))
        if unknown_analysis:
            raise ValueError(f"Planner selected unknown analysis tasks: {unknown_analysis}")

    def _apply_limits(self, config: dict[str, Any]) -> None:
        config["training"]["epochs"] = min(50, max(1, int(config["training"]["epochs"])))
        params = config["representation"].setdefault("params", {})
        if "embedding_dim" in params:
            params["embedding_dim"] = min(128, max(1, int(params["embedding_dim"])))
