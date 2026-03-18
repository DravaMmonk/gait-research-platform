from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from hound_forward.agent_system.llm import StructuredJSONClient
from hound_forward.domain import ExecutionPlan, ExperimentManifest

from .experiment_planner import ExperimentManifestPlanner

logger = logging.getLogger(__name__)

OpenAIResponsesJSONClient = StructuredJSONClient


class _ManifestEnvelope(BaseModel):
    manifest: ExperimentManifest


class _ExecutionPlanEnvelope(BaseModel):
    execution_plan: ExecutionPlan


class LLMExperimentPlanner:
    """Generate manifests and execution plans with an LLM, with optional deterministic fallback."""

    def __init__(
        self,
        *,
        model: str,
        default_runner: str = "local",
        available_tools: list[dict[str, str]] | None = None,
        fallback_planner: ExperimentManifestPlanner | None = None,
    ) -> None:
        self.model = model
        self.default_runner = default_runner
        self.available_tools = list(available_tools or [])
        self.fallback_planner = fallback_planner
        self.client = StructuredJSONClient(model=model)

    def plan(self, goal: str, dataset_video_ids: list[str] | None = None) -> ExperimentManifest:
        prompt = (
            "Create a valid experiment manifest for the research goal.\n"
            f"Goal: {goal}\n"
            f"Dataset video ids: {json.dumps(dataset_video_ids or [])}\n"
            f"Default runner: {self.default_runner}\n"
            "Return JSON only."
        )
        return self._call_with_fallback(
            call_name="manifest",
            callback=lambda: _ManifestEnvelope.model_validate(
                self.client.create_json(
                    system_prompt=self._manifest_system_prompt(),
                    user_prompt=prompt,
                    schema_name="experiment_manifest_response",
                    schema=_ManifestEnvelope.model_json_schema(),
                )
            ).manifest,
            fallback=lambda: self._fallback().plan(goal=goal, dataset_video_ids=dataset_video_ids),
        )

    def plan_execution(self, goal: str, input_asset_ids: list[str] | None = None) -> ExecutionPlan:
        prompt = (
            "Create a valid execution plan for the research goal.\n"
            f"Goal: {goal}\n"
            f"Input asset ids: {json.dumps(input_asset_ids or [])}\n"
            f"Available tools: {json.dumps(self.available_tools)}\n"
            "Return JSON only."
        )
        return self._call_with_fallback(
            call_name="execution_plan",
            callback=lambda: self._validate_execution_plan(
                _ExecutionPlanEnvelope.model_validate(
                    self.client.create_json(
                        system_prompt=self._execution_plan_system_prompt(),
                        user_prompt=prompt,
                        schema_name="execution_plan_response",
                        schema=_ExecutionPlanEnvelope.model_json_schema(),
                    )
                ).execution_plan
            ),
            fallback=lambda: self._fallback().plan_execution(goal=goal, input_asset_ids=input_asset_ids),
        )

    def _validate_execution_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        available_tool_names = {tool["name"] for tool in self.available_tools}
        for stage in plan.stages:
            if stage.tool_invocation is None:
                continue
            if stage.tool_invocation.tool_name not in available_tool_names:
                raise ValueError(f"Unsupported tool selected by LLM: {stage.tool_invocation.tool_name}")
        if not plan.stages:
            raise ValueError("LLM planner returned an empty execution plan.")
        return plan

    def _fallback(self) -> ExperimentManifestPlanner:
        if self.fallback_planner is None:
            raise RuntimeError("No deterministic planner fallback is configured.")
        return self.fallback_planner

    def _call_with_fallback(self, *, call_name: str, callback: Any, fallback: Any) -> Any:
        try:
            return callback()
        except Exception as exc:
            if self.fallback_planner is None:
                raise
            logger.warning("LLM planner %s failed; using deterministic fallback: %s", call_name, exc)
            return fallback()

    def _manifest_system_prompt(self) -> str:
        return (
            "You are planning a canine gait research experiment manifest.\n"
            "Return only JSON that matches the provided schema.\n"
            "Prefer concise, valid manifests that map the goal to the existing gait research runtime.\n"
            f"Use execution_policy.runner={self.default_runner} unless there is a strong reason not to."
        )

    def _execution_plan_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {tool['name']}: input={tool['input_kind']} output={tool['output_kind']} description={tool['description']}"
            for tool in self.available_tools
        )
        return (
            "You are planning a constrained execution plan for an existing tool-based research graph.\n"
            "Return only JSON that matches the provided schema.\n"
            "You may only select tool_invocation.tool_name values from the allowed tool list below.\n"
            "Do not invent new tools, code, SQL, DSL, or free-form execution steps.\n"
            f"Allowed tools:\n{tool_descriptions}"
        )
