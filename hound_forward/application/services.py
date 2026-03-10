from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from hound_forward.domain import (
    AssetRecord,
    ExperimentManifest,
    MetricDefinition,
    MetricResult,
    RunEvent,
    RunKind,
    RunRecord,
    RunStatus,
    SessionRecord,
    ToolResponse,
)
from hound_forward.ports import ArtifactStore, Job, JobQueue, MetadataRepository, RunExecutor


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ServiceContainer:
    metadata: MetadataRepository
    artifact_store: ArtifactStore
    queue: JobQueue
    executor: RunExecutor


class ResearchPlatformService:
    """Application boundary for sessions, runs, assets, metrics, and agent tools."""

    def __init__(self, container: ServiceContainer) -> None:
        self.container = container

    def create_session(self, title: str, dog_id: str | None = None, metadata: dict[str, Any] | None = None) -> SessionRecord:
        session = SessionRecord(title=title, dog_id=dog_id, metadata=metadata or {})
        return self.container.metadata.create_session(session)

    def create_run(self, session_id: str, manifest: ExperimentManifest, run_kind: RunKind = RunKind.PIPELINE) -> RunRecord:
        session = self.container.metadata.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id}")
        run = RunRecord(session_id=session_id, run_kind=run_kind, manifest=manifest)
        saved = self.container.metadata.create_run(run)
        self.container.metadata.append_run_event(
            RunEvent(run_id=saved.run_id, status=RunStatus.PENDING, message="Run created.", payload={"manifest_id": manifest.id})
        )
        manifest_asset = self.container.artifact_store.put_json(saved.run_id, "manifest.json", manifest.model_dump(mode="json"), "manifest")
        self.container.metadata.register_asset(manifest_asset)
        return saved

    def enqueue_run(self, run_id: str) -> RunRecord:
        run = self._require_run(run_id)
        run.status = RunStatus.QUEUED
        run.updated_at = utc_now()
        self.container.metadata.update_run(run)
        self.container.metadata.append_run_event(RunEvent(run_id=run_id, status=RunStatus.QUEUED, message="Run queued."))
        self.container.queue.enqueue(Job(run_id=run.run_id, session_id=run.session_id, payload={"manifest_id": run.manifest.id}))
        return run

    def process_next_job(self) -> RunRecord | None:
        job = self.container.queue.dequeue()
        if job is None:
            return None
        run = self._require_run(job.run_id)
        run.status = RunStatus.RUNNING
        run.updated_at = utc_now()
        self.container.metadata.update_run(run)
        self.container.metadata.append_run_event(RunEvent(run_id=run.run_id, status=RunStatus.RUNNING, message="Run started."))
        try:
            summary, assets, metric_results = self.container.executor.execute(run)
            run.status = RunStatus.SUCCEEDED
            run.summary = summary
            run.error = None
            run.updated_at = utc_now()
            self.container.metadata.update_run(run)
            for asset in assets:
                self.container.metadata.register_asset(asset)
            for metric_result in metric_results:
                self.container.metadata.register_metric_result(metric_result)
            self.container.metadata.append_run_event(
                RunEvent(run_id=run.run_id, status=RunStatus.SUCCEEDED, message="Run completed.", payload=summary)
            )
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = {"type": type(exc).__name__, "message": str(exc)}
            run.updated_at = utc_now()
            self.container.metadata.update_run(run)
            self.container.metadata.append_run_event(
                RunEvent(run_id=run.run_id, status=RunStatus.FAILED, message="Run failed.", payload=run.error)
            )
        return self._require_run(run.run_id)

    def get_run(self, run_id: str) -> RunRecord:
        return self._require_run(run_id)

    def list_runs(self, session_id: str | None = None) -> list[RunRecord]:
        return self.container.metadata.list_runs(session_id=session_id)

    def list_assets(self, run_id: str) -> list[AssetRecord]:
        return self.container.metadata.list_assets(run_id)

    def register_metric_definition(
        self,
        name: str,
        version: str,
        description: str,
        config_schema: dict[str, Any] | None = None,
    ) -> MetricDefinition:
        definition = MetricDefinition(
            metric_definition_id=str(uuid4()),
            name=name,
            version=version,
            description=description,
            config_schema=config_schema or {},
        )
        return self.container.metadata.register_metric_definition(definition)

    def list_metric_definitions(self) -> list[MetricDefinition]:
        return self.container.metadata.list_metric_definitions()

    def list_metric_results(self, run_id: str | None = None) -> list[MetricResult]:
        return self.container.metadata.list_metric_results(run_id=run_id)

    def compare_runs(self, left_run_id: str, right_run_id: str) -> dict[str, Any]:
        return self.container.metadata.compare_runs(left_run_id, right_run_id)

    def tool_create_session(self, title: str, dog_id: str | None = None, metadata: dict[str, Any] | None = None) -> ToolResponse:
        session = self.create_session(title=title, dog_id=dog_id, metadata=metadata)
        return ToolResponse(ok=True, resource_id=session.session_id, status="created", data=session.model_dump(mode="json"))

    def tool_create_run(self, session_id: str, manifest: ExperimentManifest) -> ToolResponse:
        run = self.create_run(session_id=session_id, manifest=manifest)
        return ToolResponse(ok=True, resource_id=run.run_id, status=run.status.value, data=run.model_dump(mode="json"))

    def tool_enqueue_run(self, run_id: str) -> ToolResponse:
        run = self.enqueue_run(run_id)
        return ToolResponse(ok=True, resource_id=run.run_id, status=run.status.value, data=run.model_dump(mode="json"))

    def tool_get_run(self, run_id: str) -> ToolResponse:
        run = self.get_run(run_id)
        return ToolResponse(ok=True, resource_id=run.run_id, status=run.status.value, data=run.model_dump(mode="json"))

    def tool_list_runs(self, session_id: str | None = None) -> ToolResponse:
        runs = [item.model_dump(mode="json") for item in self.list_runs(session_id=session_id)]
        return ToolResponse(ok=True, status="ok", data={"runs": runs})

    def tool_get_asset(self, run_id: str) -> ToolResponse:
        assets = [item.model_dump(mode="json") for item in self.list_assets(run_id)]
        return ToolResponse(ok=True, status="ok", data={"assets": assets})

    def tool_list_metrics(self, run_id: str | None = None) -> ToolResponse:
        definitions = [item.model_dump(mode="json") for item in self.list_metric_definitions()]
        results = [item.model_dump(mode="json") for item in self.list_metric_results(run_id=run_id)]
        return ToolResponse(ok=True, status="ok", data={"definitions": definitions, "results": results})

    def tool_compare_runs(self, left_run_id: str, right_run_id: str) -> ToolResponse:
        comparison = self.compare_runs(left_run_id, right_run_id)
        return ToolResponse(ok=True, status="ok", data=comparison)

    def tool_create_metric_definition(
        self,
        name: str,
        version: str,
        description: str,
        config_schema: dict[str, Any] | None = None,
    ) -> ToolResponse:
        definition = self.register_metric_definition(name=name, version=version, description=description, config_schema=config_schema)
        return ToolResponse(ok=True, resource_id=definition.metric_definition_id, status="created", data=definition.model_dump(mode="json"))

    def tool_evaluate_metric_definition(self, run_id: str, metric_name: str) -> ToolResponse:
        matches = [item.model_dump(mode="json") for item in self.list_metric_results(run_id=run_id) if item.name == metric_name]
        return ToolResponse(ok=True, status="ok", data={"matches": matches})

    def tool_search_dataset(self, breed: str | None = None, video_ids: list[str] | None = None) -> ToolResponse:
        filters = {"breed": breed, "video_ids": video_ids or []}
        return ToolResponse(ok=True, status="ok", data={"filters": filters, "message": "Dataset search scaffold."})

    def _require_run(self, run_id: str) -> RunRecord:
        run = self.container.metadata.get_run(run_id)
        if run is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        return run
