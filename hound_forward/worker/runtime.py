from __future__ import annotations

from dataclasses import dataclass

from hound_forward.application import ResearchPlatformService


@dataclass
class PlaceholderLocalWorkerBridge:
    """Placeholder local worker bridge used only for runtime validation and tests."""

    service: ResearchPlatformService

    def drain_once(self):
        return self.service.process_next_job()
