from __future__ import annotations

from typing import Any, Callable

from hound_forward.application import ResearchPlatformService
from hound_forward.domain import ExecutionPlan, ExperimentManifest, RunKind, ToolResponse


class ToolRegistry:
    _SERVICE_TOOL_METADATA: dict[str, dict[str, str]] = {
        "create_session": {
            "description": "Create a research session before uploads or analysis runs.",
            "input_kind": "request",
            "output_kind": "session",
            "scope": "platform_registry",
        },
        "list_sessions": {
            "description": "List existing research sessions that can be selected in the console.",
            "input_kind": "none",
            "output_kind": "session_list",
            "scope": "platform_registry",
        },
        "delete_session": {
            "description": "Delete a research session and its stored run metadata.",
            "input_kind": "session_reference",
            "output_kind": "deletion_result",
            "scope": "platform_registry",
        },
        "create_run": {
            "description": "Create a run from a validated manifest and optional execution plan.",
            "input_kind": "manifest",
            "output_kind": "run",
            "scope": "platform_registry",
        },
        "get_run": {
            "description": "Read the latest stored state for a single run.",
            "input_kind": "run_id",
            "output_kind": "run",
            "scope": "platform_registry",
        },
        "list_runs": {
            "description": "List runs that belong to a session.",
            "input_kind": "session_id",
            "output_kind": "run_list",
            "scope": "platform_registry",
        },
        "read_metrics": {
            "description": "Read metric results that were produced for a completed run.",
            "input_kind": "run_id",
            "output_kind": "metric_result",
            "scope": "platform_registry",
        },
        "compare_runs": {
            "description": "Compare summaries and metrics across multiple runs.",
            "input_kind": "run_ids",
            "output_kind": "comparison_report",
            "scope": "platform_registry",
        },
        "list_session_videos": {
            "description": "List uploaded video assets available in the active research session.",
            "input_kind": "current_session",
            "output_kind": "video_list",
            "scope": "platform_registry",
        },
        "enqueue_run": {
            "description": "Queue a created run for execution by the worker bridge.",
            "input_kind": "run_id",
            "output_kind": "run",
            "scope": "platform_registry",
        },
        "console_respond": {
            "description": "Generate a console-style response for the current research context.",
            "input_kind": "chat_request",
            "output_kind": "console_response",
            "scope": "platform_registry",
        },
        "visualize_pysr_manifest": {
            "description": "Summarize a symbolic manifest for governance or review.",
            "input_kind": "manifest",
            "output_kind": "report",
            "scope": "platform_registry",
        },
    }

    def __init__(self, service: ResearchPlatformService) -> None:
        self.service = service
        self._tools: dict[str, Callable[..., ToolResponse]] = {
            "create_session": self.service.tool_create_session,
            "list_sessions": self.service.tool_list_sessions,
            "delete_session": self.service.tool_delete_session,
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

    def describe_tools(self) -> list[dict[str, str]]:
        described_tools = [
            {
                "name": name,
                **self._SERVICE_TOOL_METADATA.get(
                    name,
                    {
                        "description": "Platform registry tool.",
                        "input_kind": "unknown",
                        "output_kind": "unknown",
                        "scope": "platform_registry",
                    },
                ),
            }
            for name in sorted(self._tools)
        ]
        if self.service.container.tool_runner is None:
            return described_tools

        described_tools.extend(
            {
                **tool,
                "scope": "graph_execution",
            }
            for tool in self.service.container.tool_runner.describe_tools()
        )
        return sorted(described_tools, key=lambda item: (item["scope"], item["name"]))

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
