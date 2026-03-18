from __future__ import annotations

import time
from dataclasses import dataclass

from hound_forward.application import ResearchPlatformService
from hound_forward.domain import RunRecord, RunStatus


@dataclass
class InlineRunMonitor:
    """Local-only run monitor used for tests and single-process validation."""

    service: ResearchPlatformService

    def wait_for_terminal_state(self, run_id: str, *, max_attempts: int = 8, poll_interval_seconds: float = 0.0) -> RunRecord:
        run = self.service.get_run(run_id)
        attempts = 0
        while run.status in {RunStatus.CREATED, RunStatus.QUEUED, RunStatus.RUNNING} and attempts < max_attempts:
            processed = self.service.process_next_job()
            run = self.service.get_run(run_id)
            if processed is None and poll_interval_seconds > 0:
                time.sleep(poll_interval_seconds)
            attempts += 1
        return run


@dataclass
class PollingRunMonitor:
    """Production-style run monitor that only polls persisted state."""

    service: ResearchPlatformService

    def wait_for_terminal_state(self, run_id: str, *, max_attempts: int = 60, poll_interval_seconds: float = 1.0) -> RunRecord:
        run = self.service.get_run(run_id)
        attempts = 0
        while run.status in {RunStatus.CREATED, RunStatus.QUEUED, RunStatus.RUNNING} and attempts < max_attempts:
            if poll_interval_seconds > 0:
                time.sleep(poll_interval_seconds)
            run = self.service.get_run(run_id)
            attempts += 1
        return run


@dataclass
class QueueWorkerRuntime:
    service: ResearchPlatformService

    def run_once(self) -> RunRecord | None:
        return self.service.process_next_job()

    def run_until_idle(
        self,
        *,
        poll_interval_seconds: float = 1.0,
        max_idle_polls: int = 3,
        max_runs: int = 20,
    ) -> int:
        processed_runs = 0
        idle_polls = 0
        while processed_runs < max_runs and idle_polls < max_idle_polls:
            processed = self.run_once()
            if processed is None:
                idle_polls += 1
                if poll_interval_seconds > 0 and idle_polls < max_idle_polls:
                    time.sleep(poll_interval_seconds)
                continue
            processed_runs += 1
            idle_polls = 0
        return processed_runs
