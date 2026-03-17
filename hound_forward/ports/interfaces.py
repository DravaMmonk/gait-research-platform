from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from hound_forward.domain import (
    AssetRecord,
    FormulaDefinitionRecord,
    FormulaEvaluationRecord,
    FormulaProposalRecord,
    FormulaReviewRecord,
    MetricDefinition,
    MetricResult,
    RunEvent,
    RunRecord,
    RunStatus,
    SessionRecord,
)


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
    def list_sessions(self) -> list[SessionRecord]: ...

    @abstractmethod
    def delete_session(self, session_id: str) -> bool: ...

    @abstractmethod
    def create_run(self, run: RunRecord) -> RunRecord: ...

    @abstractmethod
    def update_run(self, run: RunRecord) -> RunRecord: ...

    @abstractmethod
    def get_run(self, run_id: str) -> RunRecord | None: ...

    @abstractmethod
    def list_runs(self, session_id: str | None = None) -> list[RunRecord]: ...

    @abstractmethod
    def get_asset(self, asset_id: str) -> AssetRecord | None: ...

    @abstractmethod
    def append_run_event(self, event: RunEvent) -> RunEvent: ...

    @abstractmethod
    def list_run_events(self, run_id: str) -> list[RunEvent]: ...

    @abstractmethod
    def register_asset(self, asset: AssetRecord) -> AssetRecord: ...

    @abstractmethod
    def list_assets(self, run_id: str) -> list[AssetRecord]: ...

    @abstractmethod
    def list_session_assets(self, session_id: str, kind: str | None = None) -> list[AssetRecord]: ...

    @abstractmethod
    def register_metric_definition(self, metric_definition: MetricDefinition) -> MetricDefinition: ...

    @abstractmethod
    def list_metric_definitions(self) -> list[MetricDefinition]: ...

    @abstractmethod
    def register_metric_result(self, metric_result: MetricResult) -> MetricResult: ...

    @abstractmethod
    def list_metric_results(self, run_id: str | None = None) -> list[MetricResult]: ...

    @abstractmethod
    def create_formula_definition(self, formula_definition: FormulaDefinitionRecord) -> FormulaDefinitionRecord: ...

    @abstractmethod
    def get_formula_definition(self, formula_definition_id: str) -> FormulaDefinitionRecord | None: ...

    @abstractmethod
    def list_formula_definitions(self) -> list[FormulaDefinitionRecord]: ...

    @abstractmethod
    def create_formula_proposal(self, proposal: FormulaProposalRecord) -> FormulaProposalRecord: ...

    @abstractmethod
    def get_formula_proposal(self, formula_proposal_id: str) -> FormulaProposalRecord | None: ...

    @abstractmethod
    def list_formula_proposals(self, formula_definition_id: str | None = None) -> list[FormulaProposalRecord]: ...

    @abstractmethod
    def create_formula_evaluation(self, evaluation: FormulaEvaluationRecord) -> FormulaEvaluationRecord: ...

    @abstractmethod
    def get_formula_evaluation(self, formula_evaluation_id: str) -> FormulaEvaluationRecord | None: ...

    @abstractmethod
    def list_formula_evaluations(self, formula_definition_id: str | None = None) -> list[FormulaEvaluationRecord]: ...

    @abstractmethod
    def create_formula_review(self, review: FormulaReviewRecord) -> FormulaReviewRecord: ...

    @abstractmethod
    def list_formula_reviews(self, formula_definition_id: str | None = None) -> list[FormulaReviewRecord]: ...

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

    @abstractmethod
    def put_bytes(
        self,
        *,
        session_id: str,
        name: str,
        content: bytes,
        kind: str,
        mime_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> AssetRecord: ...


class JobQueue(ABC):
    @abstractmethod
    def enqueue(self, job: Job) -> None: ...

    @abstractmethod
    def dequeue(self) -> Job | None: ...


class RunExecutor(ABC):
    @abstractmethod
    def execute(self, run: RunRecord) -> tuple[dict[str, Any], list[AssetRecord], list[MetricResult]]: ...


class ToolRunner(ABC):
    @abstractmethod
    def invoke(
        self,
        *,
        tool_name: str,
        input_asset: AssetRecord,
        run_id: str,
        config: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], AssetRecord]: ...

    @abstractmethod
    def describe_tools(self) -> list[dict[str, str]]: ...
