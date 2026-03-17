from __future__ import annotations

from typing import Any, Callable

from hound_forward.application import ResearchPlatformService
from hound_forward.domain import ExecutionPlan, ExperimentManifest, RunKind, ToolResponse


class ToolRegistry:
    def __init__(self, service: ResearchPlatformService) -> None:
        self.service = service
        self._tools: dict[str, Callable[..., ToolResponse]] = {
            "create_session": self.service.tool_create_session,
            "create_run": self._create_run,
            "get_run": self.service.tool_get_run,
            "list_runs": self.service.tool_list_runs,
            "read_metrics": self.service.tool_read_metrics,
            "compare_runs": self.service.tool_compare_runs,
            "list_session_videos": self._list_session_videos,
            "enqueue_run": self.service.tool_enqueue_run,
            "console_respond": self.service.tool_console_respond,
            "visualize_pysr_manifest": self.service.tool_visualize_pysr_manifest,
        }

    def call(self, name: str, **kwargs: Any) -> ToolResponse:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name](**kwargs)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def _create_run(
        self,
        session_id: str,
        manifest: dict[str, Any],
        execution_plan: dict[str, Any] | None = None,
        run_kind: str = "pipeline",
    ) -> ToolResponse:
        return self.service.tool_create_run(
            session_id=session_id,
            manifest=ExperimentManifest.model_validate(manifest),
            execution_plan=None if execution_plan is None else ExecutionPlan.model_validate(execution_plan),
            run_kind=RunKind(run_kind),
        )

    def _list_session_videos(self, session_id: str) -> ToolResponse:
        videos = [item.model_dump(mode="json") for item in self.service.list_session_videos(session_id)]
        return ToolResponse(ok=True, status="ok", data={"videos": videos})
