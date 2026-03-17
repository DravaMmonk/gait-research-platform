from __future__ import annotations

import logging

from hound_forward.settings import PlatformSettings

from .experiment_planner import ExperimentManifestPlanner
from .llm_planner import LLMExperimentPlanner
from .protocol import PlannerProtocol

logger = logging.getLogger(__name__)


def build_planner(*, settings: PlatformSettings, available_tools: list[dict[str, str]]) -> PlannerProtocol:
    deterministic = ExperimentManifestPlanner(default_runner=settings.default_runner, available_tools=available_tools)
    planner_mode = settings.planner_mode.lower()
    if planner_mode == "deterministic":
        setattr(deterministic, "planner_mode_used", "deterministic")
        return deterministic

    fallback = deterministic if planner_mode == "hybrid" else None
    try:
        planner = LLMExperimentPlanner(
            model=settings.llm_model,
            default_runner=settings.default_runner,
            available_tools=available_tools,
            fallback_planner=fallback,
        )
        setattr(planner, "planner_mode_used", planner_mode)
        return planner
    except Exception as exc:
        logger.warning("Unable to initialize LLM planner; using deterministic planner: %s", exc)
        setattr(deterministic, "planner_mode_used", "deterministic")
        return deterministic
