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


class AssetKind(StrEnum):
    VIDEO = "video"
    KEYPOINTS = "keypoints"
    SIGNAL = "signal"
    METRIC_RESULT = "metric_result"
    PLOT = "plot"
    REPORT = "report"
    MANIFEST = "manifest"
    LOG = "log"


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


class ToolResponse(BaseModel):
    ok: bool
    resource_id: str | None = None
    status: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
