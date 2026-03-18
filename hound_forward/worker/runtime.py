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

    def run_forever(self, *, poll_interval_seconds: float = 1.0) -> None:
        while True:
            processed = self.run_once()
            if processed is None and poll_interval_seconds > 0:
                time.sleep(poll_interval_seconds)
