from __future__ import annotations

from typing import Any, Callable

from hound_forward.application import ResearchPlatformService
from hound_forward.domain import ExperimentManifest, ToolResponse


class ToolRegistry:
    def __init__(self, service: ResearchPlatformService) -> None:
        self.service = service
        self._tools: dict[str, Callable[..., ToolResponse]] = {
            "create_session": self.service.tool_create_session,
            "create_run": self._create_run,
            "enqueue_run": self.service.tool_enqueue_run,
            "get_run": self.service.tool_get_run,
            "list_runs": self.service.tool_list_runs,
            "get_asset": self.service.tool_get_asset,
            "list_metrics": self.service.tool_list_metrics,
            "compare_runs": self.service.tool_compare_runs,
            "create_metric_definition": self.service.tool_create_metric_definition,
            "evaluate_metric_definition": self.service.tool_evaluate_metric_definition,
            "search_dataset": self.service.tool_search_dataset,
        }

    def call(self, name: str, **kwargs: Any) -> ToolResponse:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name](**kwargs)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def _create_run(self, session_id: str, manifest: dict[str, Any]) -> ToolResponse:
        return self.service.tool_create_run(session_id=session_id, manifest=ExperimentManifest.model_validate(manifest))
