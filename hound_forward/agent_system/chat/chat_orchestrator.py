from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from hound_forward.agent_system.graphs import ResearchGraph
from hound_forward.agent_system.planners import build_planner
from hound_forward.agent_system.tools.registry import ToolRegistry
from hound_forward.application import ResearchPlatformService
from hound_forward.domain import (
    ChatContext,
    ChatIntent,
    ChatResponse,
    ChatResponseType,
    RunDetailResponse,
    RunStatus,
    ToolTraceItem,
)
from hound_forward.settings import PlatformSettings
from hound_forward.worker.runtime import PlaceholderLocalWorkerBridge

from .intent_router import IntentRouter
from .progress import build_progress_messages
from .reasoner import ChatReasoner

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    def __init__(self, *, service: ResearchPlatformService, settings: PlatformSettings | None = None) -> None:
        self.service = service
        self.settings = settings or PlatformSettings()
        self.intent_router = IntentRouter(model=self.settings.llm_model)
        self.reasoner = ChatReasoner(model=self.settings.llm_model)

    def handle(self, *, session_id: str, message: str, context: ChatContext | None = None) -> ChatResponse:
        session = self.service.container.metadata.get_session(session_id)
        if session is None:
            return ChatResponse(type=ChatResponseType.ERROR, message=f"Unknown session_id: {session_id}")

        intent = self.intent_router.classify(message=message, context=context)
        logger.info("Chat orchestrator handling intent=%s session_id=%s", intent.value, session_id)
        if intent == ChatIntent.RUN_ANALYSIS:
            return self._run_analysis(session_id=session_id, message=message)
        if intent == ChatIntent.EXPLAIN_RESULT:
            return self._explain_result(session_id=session_id, message=message, context=context)
        return self._answer_question(session_id=session_id, message=message)

    def _run_analysis(self, *, session_id: str, message: str) -> ChatResponse:
        planner = self._build_planner()
        manifest = planner.plan(goal=message)
        execution_plan = planner.plan_execution(goal=message)
        progress_messages = build_progress_messages(execution_plan)
        graph = self._build_graph(planner=planner)
        graph_state = graph.invoke(
            goal=message,
            session_id=session_id,
            manifest=manifest.model_dump(mode="json"),
            execution_plan=execution_plan.model_dump(mode="json"),
        )
        run_id = graph_state["run_id"]
        run_detail = self.service.get_run_detail(run_id)
        structured_data = self._build_run_structured_data(
            run_detail=run_detail,
            manifest=graph_state.get("manifest", manifest.model_dump(mode="json")),
            execution_plan=graph_state.get("execution_plan", execution_plan.model_dump(mode="json")),
            recommendation=graph_state.get("recommendation"),
            intent=ChatIntent.RUN_ANALYSIS,
        )
        explanation = self.reasoner.explain_result(message=message, result_payload=structured_data)
        logger.info(
            "Chat orchestrator completed run_analysis run_id=%s stage_count=%s",
            run_id,
            len(structured_data.get("stage_results", [])),
        )
        return ChatResponse(
            type=ChatResponseType.RUN,
            message=explanation,
            run_id=run_id,
            progress_messages=progress_messages,
            structured_data=structured_data,
        )

    def _explain_result(self, *, session_id: str, message: str, context: ChatContext | None) -> ChatResponse:
        source_run = self._resolve_source_run(session_id=session_id, context=context)
        if source_run is None:
            return self._answer_question(session_id=session_id, message=message)
        run_detail = self.service.get_run_detail(source_run.run_id)
        structured_data = {
            "intent": ChatIntent.EXPLAIN_RESULT.value,
            "source_run_id": run_detail.run.run_id,
            "run_summary": run_detail.run.summary,
            "metrics": [metric.model_dump(mode="json") for metric in run_detail.metrics],
            "tool_trace": [item.model_dump(mode="json") for item in self._build_tool_trace(run_detail=run_detail)],
        }
        explanation = self.reasoner.explain_result(message=message, result_payload=structured_data)
        logger.info("Chat orchestrator explained run_id=%s", run_detail.run.run_id)
        return ChatResponse(
            type=ChatResponseType.TEXT,
            message=explanation,
            run_id=run_detail.run.run_id,
            structured_data=structured_data,
        )

    def _answer_question(self, *, session_id: str, message: str) -> ChatResponse:
        session = self.service.container.metadata.get_session(session_id)
        runs = self.service.list_runs(session_id=session_id)
        available_tools = ToolRegistry(self.service).describe_tools()
        current_session_videos = [
            {
                "asset_id": asset.asset_id,
                "file_name": Path(asset.blob_path).name,
                "mime_type": asset.mime_type,
                "created_at": asset.created_at.isoformat(),
            }
            for asset in self.service.list_session_videos(session_id)
        ]
        session_summary = {
            "session_id": session_id,
            "session_title": session.title if session is not None else "unknown",
            "run_count": len(runs),
            "latest_completed_run_id": next((run.run_id for run in reversed(runs) if run.status == RunStatus.COMPLETED), None),
            "available_tool_count": len(available_tools),
            "video_asset_count": len(current_session_videos),
        }
        if self._is_current_session_video_question(message):
            answer = self._describe_current_session_videos(current_session_videos)
        elif self._is_tool_inventory_question(message):
            answer = self.reasoner.describe_tools(
                message=message,
                session_summary=session_summary,
                available_tools=available_tools,
            )
        else:
            answer = self.reasoner.answer_question(
                message=message,
                session_summary=session_summary,
                available_tools=available_tools,
            )
        return ChatResponse(
            type=ChatResponseType.TEXT,
            message=answer,
            structured_data={
                "intent": ChatIntent.ASK_QUESTION.value,
                "context": session_summary,
                "available_tools": available_tools,
                "current_session_videos": current_session_videos,
            },
        )

    def _build_planner(self) -> Any:
        available_tools = self.service.container.tool_runner.describe_tools() if self.service.container.tool_runner else []
        planner = build_planner(settings=self.settings, available_tools=available_tools)
        logger.info("Planner mode selected: %s", getattr(planner, "planner_mode_used", self.settings.planner_mode))
        return planner

    def _build_graph(self, *, planner: Any) -> ResearchGraph:
        return ResearchGraph(
            planner=planner,
            tools=ToolRegistry(self.service),
            worker_bridge=PlaceholderLocalWorkerBridge(service=self.service),
        )

    def _resolve_source_run(self, *, session_id: str, context: ChatContext | None):
        if context is not None and context.run_id is not None:
            return self.service.get_run(context.run_id)
        completed = [run for run in self.service.list_runs(session_id=session_id) if run.status == RunStatus.COMPLETED]
        if not completed:
            return None
        return sorted(completed, key=lambda item: item.created_at)[-1]

    def _build_run_structured_data(
        self,
        *,
        run_detail: RunDetailResponse,
        manifest: dict[str, Any],
        execution_plan: dict[str, Any],
        recommendation: str | None,
        intent: ChatIntent,
    ) -> dict[str, Any]:
        metric_names = [metric.name for metric in run_detail.metrics]
        return {
            "intent": intent.value,
            "manifest": manifest,
            "execution_plan": execution_plan,
            "run_summary": run_detail.run.summary,
            "metrics": [metric.model_dump(mode="json") for metric in run_detail.metrics],
            "stage_results": [stage.model_dump(mode="json") for stage in run_detail.run.stage_results],
            "tool_trace": [item.model_dump(mode="json") for item in self._build_tool_trace(run_detail=run_detail)],
            "evidence_context": {
                "metric_definition": ", ".join(metric_names) if metric_names else "no_metrics",
                "time_range": "current run",
                "data_quality": "Metrics were produced by the executed research graph.",
                "clinician_reviewed": False,
                "derived_metric": bool(metric_names),
                "references": [run_detail.run.run_id, *run_detail.run.input_asset_ids[:1]],
            },
            "recommendation": recommendation or run_detail.run.summary.get("last_stage_summary", {}).get("recommendations", [""])[0],
        }

    @staticmethod
    def _build_tool_trace(*, run_detail: RunDetailResponse) -> list[ToolTraceItem]:
        items = [
            ToolTraceItem(
                tool_name="graph_execution",
                purpose="Execute the constrained research graph for the user request.",
                status=run_detail.run.status.value,
                details={"run_id": run_detail.run.run_id, "run_kind": run_detail.run.run_kind.value},
            )
        ]
        if run_detail.run.execution_plan is not None:
            items.extend(
                ToolTraceItem(
                    tool_name=stage.tool_invocation.tool_name if stage.tool_invocation is not None else stage.name,
                    purpose=f"Execute stage {stage.name}.",
                    status=(
                        run_detail.run.stage_results[index].status.value
                        if index < len(run_detail.run.stage_results)
                        else run_detail.run.status.value
                    ),
                    details={"stage_id": stage.stage_id, "stage_type": stage.stage_type.value},
                )
                for index, stage in enumerate(run_detail.run.execution_plan.stages)
            )
        return items

    @staticmethod
    def _is_tool_inventory_question(message: str) -> bool:
        normalized = message.lower()
        inventory_markers = (
            "what tools",
            "which tools",
            "available tools",
            "callable tools",
            "tool registry",
            "what can you call",
            "what can you use",
            "capabilities",
            "can you invoke",
        )
        return any(marker in normalized for marker in inventory_markers)

    @staticmethod
    def _is_current_session_video_question(message: str) -> bool:
        normalized = message.lower()
        if "video" not in normalized:
            return False
        return any(
            marker in normalized
            for marker in (
                "current session",
                "this session",
                "uploaded video",
                "uploaded videos",
                "video assets",
                "available video",
                "available videos",
                "list videos",
            )
        )

    @staticmethod
    def _describe_current_session_videos(current_session_videos: list[dict[str, str]]) -> str:
        if not current_session_videos:
            return "The current session has no uploaded video assets yet."

        lines = ["Uploaded video assets in the current session:"]
        for video in current_session_videos:
            lines.append(f"- {video['file_name']} ({video['mime_type']}, asset {video['asset_id']})")
        return "\n".join(lines)
