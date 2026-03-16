from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunKind(StrEnum):
    PIPELINE = "pipeline"
    METRIC_EVALUATION = "metric_evaluation"
    AGENT_ANALYSIS = "agent_analysis"
    EXPERIMENT_COMPARISON = "experiment_comparison"
    FORMULA_PROPOSAL = "formula_proposal"
    FORMULA_EVALUATION = "formula_evaluation"
    FORMULA_REVIEW = "formula_review"


class AssetKind(StrEnum):
    VIDEO = "video"
    KEYPOINTS = "keypoints"
    SIGNAL = "signal"
    METRIC_RESULT = "metric_result"
    PLOT = "plot"
    REPORT = "report"
    MANIFEST = "manifest"
    LOG = "log"
    EVALUATION = "evaluation"
    FORMULA = "formula"
    REVIEW = "review"


class FormulaStatus(StrEnum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    UNDER_EVALUATION = "under_evaluation"
    REVIEW_PENDING = "review_pending"
    APPROVED_FOR_RESEARCH = "approved_for_research"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class ReviewVerdict(StrEnum):
    ACCEPTED_FOR_FURTHER_VALIDATION = "accepted_for_further_validation"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    CLINICALLY_INTERESTING_BUT_UNPROVEN = "clinically_interesting_but_unproven"


class ExecutionStageType(StrEnum):
    PLACEHOLDER_PIPELINE = "placeholder_pipeline"
    RESEARCH_TOOL = "research_tool"
    FORMULA_EVALUATOR = "formula_evaluator"


class DatasetSelector(BaseModel):
    dog_ids: list[str] = Field(default_factory=list)
    session_ids: list[str] = Field(default_factory=list)
    video_ids: list[str] = Field(default_factory=list)
    breed: str | None = None


class PipelineSpec(BaseModel):
    experiment_name: str = "contrastive_training"
    keypoint_model: str = "gait_pose_v3"
    signal_names: list[str] = Field(default_factory=lambda: ["velocity_signal"])
    representation_model: str = "temporal_embedding"
    parameters: dict[str, Any] = Field(default_factory=dict)


class MetricSpec(BaseModel):
    name: str
    version: str = "v1"
    config: dict[str, Any] = Field(default_factory=dict)


class AnalysisSpec(BaseModel):
    name: str
    config: dict[str, Any] = Field(default_factory=dict)


class ExecutionPolicy(BaseModel):
    runner: str = "local"
    priority: str = "normal"
    use_gpu: bool = False


class EvaluationInputSpec(BaseModel):
    signal_names: list[str] = Field(default_factory=list)
    metric_names: list[str] = Field(default_factory=list)
    input_asset_ids: list[str] = Field(default_factory=list)


class EvaluationOutputSpec(BaseModel):
    artifact_kinds: list[str] = Field(default_factory=list)
    summary_keys: list[str] = Field(default_factory=list)


class ToolInvocationRecord(BaseModel):
    tool_name: str
    input_asset_id: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    output_name: str | None = None
    artifact_kind: str | None = None


class ExecutionStage(BaseModel):
    stage_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    stage_type: ExecutionStageType
    tool_invocation: ToolInvocationRecord | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    stages: list[ExecutionStage] = Field(default_factory=list)


class StageResult(BaseModel):
    stage_id: str
    name: str
    status: RunStatus
    produced_asset_ids: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class ExperimentManifest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    dataset: DatasetSelector = Field(default_factory=DatasetSelector)
    pipeline: PipelineSpec = Field(default_factory=PipelineSpec)
    metrics: list[MetricSpec] = Field(default_factory=list)
    analysis: list[AnalysisSpec] = Field(default_factory=list)
    execution_policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    tags: list[str] = Field(default_factory=list)
    goal: str | None = None
    input_asset_ids: list[str] = Field(default_factory=list)
    evaluation_input: EvaluationInputSpec = Field(default_factory=EvaluationInputSpec)
    evaluation_output: EvaluationOutputSpec = Field(default_factory=EvaluationOutputSpec)


class SessionRecord(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    dog_id: str | None = None
    title: str
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class RunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    run_kind: RunKind = RunKind.PIPELINE
    status: RunStatus = RunStatus.CREATED
    manifest: ExperimentManifest
    input_asset_ids: list[str] = Field(default_factory=list)
    execution_plan: ExecutionPlan | None = None
    stage_results: list[StageResult] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RunEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    status: RunStatus
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class AssetRecord(BaseModel):
    asset_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str | None = None
    session_id: str | None = None
    kind: AssetKind
    blob_path: str
    checksum: str
    mime_type: str = "application/json"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class VideoUploadResponse(BaseModel):
    session_id: str
    asset: AssetRecord
    placeholder_flags: dict[str, bool] = Field(
        default_factory=lambda: {"dummy": True, "fake": True, "placeholder": True}
    )


class MetricReadResponse(BaseModel):
    run_id: str
    metric_results: list[MetricResult] = Field(default_factory=list)
    metrics_asset: AssetRecord | None = None
    placeholder_flags: dict[str, bool] = Field(
        default_factory=lambda: {"dummy": True, "fake": True, "placeholder": True}
    )


class RunDetailResponse(BaseModel):
    run: RunRecord
    assets: list[AssetRecord] = Field(default_factory=list)
    metrics: list[MetricResult] = Field(default_factory=list)
    events: list[RunEvent] = Field(default_factory=list)
    placeholder_flags: dict[str, bool] = Field(
        default_factory=lambda: {"dummy": True, "fake": True, "placeholder": True}
    )


class DummyPipelineOutput(BaseModel):
    keypoints: dict[str, Any]
    metrics: dict[str, Any]
    report: dict[str, Any]
    placeholder_flags: dict[str, bool] = Field(
        default_factory=lambda: {"dummy": True, "fake": True, "placeholder": True}
    )


class MetricDefinition(BaseModel):
    metric_definition_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    version: str
    description: str
    config_schema: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class MetricResult(BaseModel):
    metric_result_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    metric_definition_id: str
    name: str
    version: str
    value: float
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class FormulaDefinitionRecord(BaseModel):
    formula_definition_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    version: str
    status: FormulaStatus = FormulaStatus.DRAFT
    description: str
    input_requirements: dict[str, Any] = Field(default_factory=dict)
    execution_spec: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class FormulaProposalRecord(BaseModel):
    formula_proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    formula_definition_id: str | None = None
    source_run_id: str | None = None
    research_question: str
    proposal_payload: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class FormulaEvaluationRecord(BaseModel):
    formula_evaluation_id: str = Field(default_factory=lambda: str(uuid4()))
    formula_definition_id: str
    run_id: str
    dataset_ref: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ReviewEvidenceBundle(BaseModel):
    run_id: str | None = None
    asset_ids: list[str] = Field(default_factory=list)
    metric_result_ids: list[str] = Field(default_factory=list)
    references: dict[str, Any] = Field(default_factory=dict)


class FormulaReviewRecord(BaseModel):
    formula_review_id: str = Field(default_factory=lambda: str(uuid4()))
    formula_definition_id: str
    formula_evaluation_id: str | None = None
    reviewer_id: str
    verdict: ReviewVerdict
    notes: str
    evidence_bundle: ReviewEvidenceBundle = Field(default_factory=ReviewEvidenceBundle)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ToolResponse(BaseModel):
    ok: bool
    resource_id: str | None = None
    status: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
