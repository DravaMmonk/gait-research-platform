from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from hound_forward.agent_system.graphs import ResearchGraph
from hound_forward.agent_system.planners import build_planner
from hound_forward.agent_system.tools.registry import ToolRegistry
from hound_forward.application import ResearchPlatformService
from hound_forward.domain import JobType
from hound_forward.ports import Job
from hound_forward.settings import PlatformSettings
from hound_forward.worker.runtime import InlineRunMonitor, PollingRunMonitor


@dataclass
class AgentRuntime:
    service: ResearchPlatformService
    settings: PlatformSettings

    def run_next_job(self) -> dict[str, Any] | None:
        message = self.service.container.agent_queue.dequeue()
        if message is None:
            return None
        return self.run_job(message)

    def run_job(self, message: Job) -> dict[str, Any]:
        job = self.service.start_job(message.job_id)
        try:
            result = self.run_payload(job.payload)
            final_job = self.service.complete_job(job.job_id, result=result, run_id=result.get("run_id"))
            return {"job_id": final_job.job_id, "status": final_job.status.value, "result": final_job.result}
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
            failed_job = self.service.fail_job(job.job_id, error=error)
            return {"job_id": failed_job.job_id, "status": failed_job.status.value, "error": failed_job.error}

    def run_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        planner = build_planner(
            settings=self.settings,
            available_tools=self.service.container.tool_runner.describe_tools() if self.service.container.tool_runner else [],
        )
        run_monitor = (
            InlineRunMonitor(service=self.service)
            if self.settings.placeholder_worker_mode
            else PollingRunMonitor(service=self.service)
        )
        graph = ResearchGraph(
            planner=planner,
            tools=ToolRegistry(self.service),
            run_monitor=run_monitor,
        )
        graph_state = graph.invoke(goal=payload["goal"], session_id=payload["session_id"])
        run_id = graph_state["run_id"]
        run_detail = self.service.get_run_detail(run_id)
        return {
            "job_type": JobType.AGENT_EXECUTION.value,
            "session_id": payload["session_id"],
            "goal": payload["goal"],
            "run_id": run_id,
            "run_status": run_detail.run.status.value,
            "recommendation": graph_state.get("recommendation"),
            "run_summary": run_detail.run.summary,
            "metrics": [metric.model_dump(mode="json") for metric in run_detail.metrics],
        }

    def run_forever(self) -> None:
        while True:
            processed = self.run_next_job()
            if processed is None and self.settings.queue.poll_interval_seconds > 0:
                time.sleep(self.settings.queue.poll_interval_seconds)
