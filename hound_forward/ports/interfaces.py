from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from hound_forward.domain import AssetRecord, MetricDefinition, MetricResult, RunEvent, RunRecord, RunStatus, SessionRecord


@dataclass
class Job:
    run_id: str
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)


class MetadataRepository(ABC):
    @abstractmethod
    def create_session(self, session: SessionRecord) -> SessionRecord: ...

    @abstractmethod
    def get_session(self, session_id: str) -> SessionRecord | None: ...

    @abstractmethod
    def create_run(self, run: RunRecord) -> RunRecord: ...

    @abstractmethod
    def update_run(self, run: RunRecord) -> RunRecord: ...

    @abstractmethod
    def get_run(self, run_id: str) -> RunRecord | None: ...

    @abstractmethod
    def list_runs(self, session_id: str | None = None) -> list[RunRecord]: ...

    @abstractmethod
    def append_run_event(self, event: RunEvent) -> RunEvent: ...

    @abstractmethod
    def list_run_events(self, run_id: str) -> list[RunEvent]: ...

    @abstractmethod
    def register_asset(self, asset: AssetRecord) -> AssetRecord: ...

    @abstractmethod
    def list_assets(self, run_id: str) -> list[AssetRecord]: ...

    @abstractmethod
    def register_metric_definition(self, metric_definition: MetricDefinition) -> MetricDefinition: ...

    @abstractmethod
    def list_metric_definitions(self) -> list[MetricDefinition]: ...

    @abstractmethod
    def register_metric_result(self, metric_result: MetricResult) -> MetricResult: ...

    @abstractmethod
    def list_metric_results(self, run_id: str | None = None) -> list[MetricResult]: ...

    def compare_runs(self, left_run_id: str, right_run_id: str) -> dict[str, Any]:
        left = {item.name: item.value for item in self.list_metric_results(left_run_id)}
        right = {item.name: item.value for item in self.list_metric_results(right_run_id)}
        names = sorted(set(left) | set(right))
        return {
            "left_run_id": left_run_id,
            "right_run_id": right_run_id,
            "metrics": [
                {
                    "name": name,
                    "left": left.get(name),
                    "right": right.get(name),
                    "delta": None if left.get(name) is None or right.get(name) is None else right[name] - left[name],
                }
                for name in names
            ],
        }


class ArtifactStore(ABC):
    @abstractmethod
    def put_json(self, run_id: str, name: str, payload: dict[str, Any], kind: str) -> AssetRecord: ...


class JobQueue(ABC):
    @abstractmethod
    def enqueue(self, job: Job) -> None: ...

    @abstractmethod
    def dequeue(self) -> Job | None: ...


class RunExecutor(ABC):
    @abstractmethod
    def execute(self, run: RunRecord) -> tuple[dict[str, Any], list[AssetRecord], list[MetricResult]]: ...
