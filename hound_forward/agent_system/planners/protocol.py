from __future__ import annotations

from typing import Protocol

from hound_forward.domain import ExecutionPlan, ExperimentManifest


class PlannerProtocol(Protocol):
    def plan(self, goal: str, dataset_video_ids: list[str] | None = None) -> ExperimentManifest: ...

    def plan_execution(self, goal: str, input_asset_ids: list[str] | None = None) -> ExecutionPlan: ...
