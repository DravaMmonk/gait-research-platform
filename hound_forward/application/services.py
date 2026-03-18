from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from hound_forward.agent_tools import summarize_manifest

from hound_forward.domain import (
    ActiveContext,
    AssetKind,
    AssetRecord,
    ComparisonCardItem,
    ComparisonCardsModule,
    ComparisonCardsPayload,
    ConsoleAgentResponse,
    ConsoleThreadMessage,
    ConsoleViewMode,
    DisplayPreference,
    EvidenceContext,
    EvidencePanelModule,
    EvidencePanelPayload,
    ExecutionPlan,
    ExecutionStage,
    ExecutionStageType,
    ExperimentManifest,
    FormulaDefinitionRecord,
    FormulaExplanationModule,
    FormulaExplanationPayload,
    FormulaEvaluationRecord,
    FormulaProposalRecord,
    FormulaReviewRecord,
    FormulaStatus,
    HighlightItem,
    JobRecord,
    JobStatus,
    JobType,
    MetricDefinition,
    MetricTableColumn,
    MetricTableModule,
    MetricTablePayload,
    MetricTableRow,
    MetricReadResponse,
    MetricResult,
    ReviewEvidenceBundle,
    ReviewVerdict,
    RunDetailResponse,
    RunEvent,
    RunKind,
    RunRecord,
    RunStatus,
    SessionRecord,
    SessionAttachmentUploadResponse,
    SummaryCardModule,
    SummaryCardPayload,
    StageResult,
    ToolTraceItem,
    ToolInvocationRecord,
    ToolResponse,
    TrendChartModule,
    TrendChartPayload,
    VideoPanelModule,
    VideoPanelPayload,
)
from hound_forward.ports import ArtifactStore, Job, JobQueue, MetadataRepository, RunExecutor, ToolRunner
from hound_forward.settings import PlatformSettings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ServiceContainer:
    metadata: MetadataRepository
    artifact_store: ArtifactStore
    run_queue: JobQueue
    agent_queue: JobQueue
    executor: RunExecutor
    tool_runner: ToolRunner | None = None


class ResearchPlatformService:
    """Application boundary for sessions, runs, assets, metrics, and agent tools."""

    def __init__(self, container: ServiceContainer) -> None:
        self.container = container

    def create_session(self, title: str, dog_id: str | None = None, metadata: dict[str, Any] | None = None) -> SessionRecord:
        session = SessionRecord(title=title, dog_id=dog_id, metadata=metadata or {})
        return self.container.metadata.create_session(session)

    def list_sessions(self) -> list[SessionRecord]:
        return self.container.metadata.list_sessions()

    def delete_session(self, session_id: str) -> bool:
        deleted = self.container.metadata.delete_session(session_id)
        if not deleted:
            raise KeyError(f"Unknown session_id: {session_id}")
        return True

    def create_run(
        self,
        session_id: str,
        manifest: ExperimentManifest,
        run_kind: RunKind = RunKind.PIPELINE,
        execution_plan: ExecutionPlan | None = None,
    ) -> RunRecord:
        session = self.container.metadata.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id}")
        if not manifest.input_asset_ids:
            raise ValueError("Run creation requires at least one input asset id for runtime validation.")
        for asset_id in manifest.input_asset_ids:
            asset = self.container.metadata.get_asset(asset_id)
            if asset is None or asset.session_id != session_id:
                raise KeyError(f"Unknown session-scoped input asset: {asset_id}")
        run = RunRecord(
            session_id=session_id,
            run_kind=run_kind,
            manifest=manifest,
            input_asset_ids=list(manifest.input_asset_ids),
            execution_plan=execution_plan or self._build_default_execution_plan(run_kind=run_kind, manifest=manifest),
        )
        saved = self.container.metadata.create_run(run)
        self.container.metadata.append_run_event(
            RunEvent(run_id=saved.run_id, status=RunStatus.CREATED, message="Run created.", payload={"manifest_id": manifest.id})
        )
        manifest_asset = self.container.artifact_store.put_json(saved.run_id, "manifest.json", manifest.model_dump(mode="json"), "manifest")
        self.container.metadata.register_asset(manifest_asset)
        return saved

    def upload_session_attachment(
        self,
        *,
        session_id: str,
        file_name: str,
        content: bytes,
        mime_type: str,
    ) -> SessionAttachmentUploadResponse:
        session = self.container.metadata.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id}")
        asset_kind = self._resolve_session_attachment_kind(file_name=file_name, mime_type=mime_type)
        asset = self.container.artifact_store.put_bytes(
            session_id=session_id,
            name=self._build_session_attachment_name(file_name),
            content=content,
            kind=asset_kind.value,
            mime_type=mime_type,
            metadata={
                "original_file_name": file_name,
                "placeholder_flags": {"dummy": True, "fake": False, "placeholder": True},
                "runtime_validation": True,
            },
        )
        registered = self.container.metadata.register_asset(asset)
        return SessionAttachmentUploadResponse(session_id=session_id, asset=registered)

    def upload_session_video(
        self,
        *,
        session_id: str,
        file_name: str,
        content: bytes,
        mime_type: str = "video/mp4",
    ) -> SessionAttachmentUploadResponse:
        if self._resolve_session_attachment_kind(file_name=file_name, mime_type=mime_type) != AssetKind.VIDEO:
            raise ValueError("Video upload endpoint only accepts video files.")
        return self.upload_session_attachment(
            session_id=session_id,
            file_name=file_name,
            content=content,
            mime_type=mime_type,
        )

    def list_session_attachments(self, session_id: str, kind: str | None = None) -> list[AssetRecord]:
        return self.container.metadata.list_session_assets(session_id=session_id, kind=kind)

    def list_session_videos(self, session_id: str) -> list[AssetRecord]:
        return self.list_session_attachments(session_id=session_id, kind="video")

    def create_job(
        self,
        *,
        job_type: JobType,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
        run_id: str | None = None,
    ) -> JobRecord:
        job = JobRecord(
            job_type=job_type,
            session_id=session_id,
            run_id=run_id,
            payload=payload,
            metadata=metadata or {},
        )
        return self.container.metadata.create_job(job)

    def get_job(self, job_id: str) -> JobRecord:
        job = self.container.metadata.get_job(job_id)
        if job is None:
            raise KeyError(f"Unknown job_id: {job_id}")
        return job

    def list_jobs(
        self,
        *,
        session_id: str | None = None,
        run_id: str | None = None,
        job_type: JobType | None = None,
    ) -> list[JobRecord]:
        return self.container.metadata.list_jobs(
            session_id=session_id,
            run_id=run_id,
            job_type=job_type.value if job_type else None,
        )

    def start_job(self, job_id: str, *, run_id: str | None = None) -> JobRecord:
        job = self.get_job(job_id)
        return self._update_job_state(job, status=JobStatus.RUNNING, run_id=run_id)

    def complete_job(self, job_id: str, *, result: dict[str, Any], run_id: str | None = None) -> JobRecord:
        job = self.get_job(job_id)
        return self._update_job_state(job, status=JobStatus.COMPLETED, result=result, run_id=run_id)

    def fail_job(self, job_id: str, *, error: dict[str, Any], run_id: str | None = None) -> JobRecord:
        job = self.get_job(job_id)
        return self._update_job_state(job, status=JobStatus.FAILED, error=error, run_id=run_id)

    def enqueue_run(self, run_id: str) -> RunRecord:
        run = self._require_run(run_id)
        run.status = RunStatus.QUEUED
        run.updated_at = utc_now()
        self.container.metadata.update_run(run)
        self.container.metadata.append_run_event(RunEvent(run_id=run_id, status=RunStatus.QUEUED, message="Run queued."))
        job = self.create_job(
            job_type=JobType.RUN_EXECUTION,
            session_id=run.session_id,
            run_id=run.run_id,
            payload={"manifest_id": run.manifest.id, "run_id": run.run_id},
            metadata={"run_kind": run.run_kind.value},
        )
        self.container.run_queue.enqueue(
            Job(
                job_id=job.job_id,
                job_type=job.job_type.value,
                run_id=run.run_id,
                session_id=run.session_id,
                payload=job.payload,
                metadata=job.metadata,
            )
        )
        return run

    def submit_agent_job(
        self,
        *,
        session_id: str,
        goal: str,
        user_id: str | None = None,
        trace_id: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> JobRecord:
        session = self.container.metadata.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id}")
        job = self.create_job(
            job_type=JobType.AGENT_EXECUTION,
            session_id=session_id,
            payload={
                "session_id": session_id,
                "goal": goal,
                "config": config or {},
            },
            metadata={
                "user_id": user_id,
                "trace_id": trace_id or str(uuid4()),
                "submitted_at": utc_now().isoformat(),
            },
        )
        self.container.agent_queue.enqueue(
            Job(
                job_id=job.job_id,
                job_type=job.job_type.value,
                run_id="",
                session_id=session_id,
                payload=job.payload,
                metadata=job.metadata,
            )
        )
        return job

    def process_next_job(self) -> RunRecord | None:
        job = self.container.run_queue.dequeue()
        if job is not None:
            run = self._require_run(job.run_id)
            run_job = self.get_job(job.job_id)
        else:
            run = self._find_next_queued_run()
            if run is None:
                return None
            queued_jobs = self.list_jobs(run_id=run.run_id, job_type=JobType.RUN_EXECUTION)
            run_job = queued_jobs[0] if queued_jobs else None
        run.status = RunStatus.RUNNING
        run.updated_at = utc_now()
        self.container.metadata.update_run(run)
        self.container.metadata.append_run_event(RunEvent(run_id=run.run_id, status=RunStatus.RUNNING, message="Run started."))
        if run_job is not None:
            self._update_job_state(run_job, status=JobStatus.RUNNING)
        try:
            summary, assets, metric_results = self.container.executor.execute(run)
            run.status = RunStatus.COMPLETED
            run.summary = summary
            run.error = None
            run.stage_results = self._build_stage_results(run=run, assets=assets, summary=summary)
            run.updated_at = utc_now()
            self.container.metadata.update_run(run)
            for asset in assets:
                self.container.metadata.register_asset(asset)
            for metric_result in metric_results:
                self.container.metadata.register_metric_result(metric_result)
            self.container.metadata.append_run_event(
                RunEvent(run_id=run.run_id, status=RunStatus.COMPLETED, message="Run completed.", payload=summary)
            )
            if run_job is not None:
                self._update_job_state(
                    run_job,
                    status=JobStatus.COMPLETED,
                    result={"run_id": run.run_id, "status": run.status.value, "summary": run.summary},
                )
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = {"type": type(exc).__name__, "message": str(exc)}
            run.updated_at = utc_now()
            self.container.metadata.update_run(run)
            self.container.metadata.append_run_event(
                RunEvent(run_id=run.run_id, status=RunStatus.FAILED, message="Run failed.", payload=run.error)
            )
            if run_job is not None:
                self._update_job_state(run_job, status=JobStatus.FAILED, error=run.error)
        return self._require_run(run.run_id)

    def get_run(self, run_id: str) -> RunRecord:
        return self._require_run(run_id)

    def list_runs(self, session_id: str | None = None) -> list[RunRecord]:
        return self.container.metadata.list_runs(session_id=session_id)

    def list_assets(self, run_id: str) -> list[AssetRecord]:
        return self.container.metadata.list_assets(run_id)

    def get_run_detail(self, run_id: str) -> RunDetailResponse:
        run = self.get_run(run_id)
        input_assets = [
            asset for asset_id in run.input_asset_ids if (asset := self.container.metadata.get_asset(asset_id)) is not None
        ]
        run_assets = self.list_assets(run_id)
        return RunDetailResponse(
            run=run,
            assets=input_assets + run_assets,
            metrics=self.list_metric_results(run_id),
            events=self.container.metadata.list_run_events(run_id),
        )

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

    def create_formula_definition(
        self,
        *,
        name: str,
        version: str,
        description: str,
        input_requirements: dict[str, Any] | None = None,
        execution_spec: dict[str, Any] | None = None,
        status: FormulaStatus = FormulaStatus.DRAFT,
    ) -> FormulaDefinitionRecord:
        record = FormulaDefinitionRecord(
            name=name,
            version=version,
            status=status,
            description=description,
            input_requirements=input_requirements or {},
            execution_spec=execution_spec or {},
        )
        return self.container.metadata.create_formula_definition(record)

    def list_formula_definitions(self) -> list[FormulaDefinitionRecord]:
        return self.container.metadata.list_formula_definitions()

    def get_formula_definition(self, formula_definition_id: str) -> FormulaDefinitionRecord:
        record = self.container.metadata.get_formula_definition(formula_definition_id)
        if record is None:
            raise KeyError(f"Unknown formula_definition_id: {formula_definition_id}")
        return record

    def create_formula_proposal(
        self,
        *,
        research_question: str,
        proposal_payload: dict[str, Any],
        formula_definition_id: str | None = None,
        source_run_id: str | None = None,
    ) -> FormulaProposalRecord:
        record = FormulaProposalRecord(
            formula_definition_id=formula_definition_id,
            source_run_id=source_run_id,
            research_question=research_question,
            proposal_payload=proposal_payload,
        )
        return self.container.metadata.create_formula_proposal(record)

    def list_formula_proposals(self, formula_definition_id: str | None = None) -> list[FormulaProposalRecord]:
        return self.container.metadata.list_formula_proposals(formula_definition_id=formula_definition_id)

    def create_formula_evaluation(
        self,
        *,
        formula_definition_id: str,
        run_id: str,
        dataset_ref: str | None = None,
        summary: dict[str, Any] | None = None,
    ) -> FormulaEvaluationRecord:
        self.get_formula_definition(formula_definition_id)
        self.get_run(run_id)
        record = FormulaEvaluationRecord(
            formula_definition_id=formula_definition_id,
            run_id=run_id,
            dataset_ref=dataset_ref,
            summary=summary or {},
        )
        return self.container.metadata.create_formula_evaluation(record)

    def list_formula_evaluations(self, formula_definition_id: str | None = None) -> list[FormulaEvaluationRecord]:
        return self.container.metadata.list_formula_evaluations(formula_definition_id=formula_definition_id)

    def create_formula_review(
        self,
        *,
        formula_definition_id: str,
        reviewer_id: str,
        verdict: ReviewVerdict,
        notes: str,
        formula_evaluation_id: str | None = None,
        evidence_bundle: ReviewEvidenceBundle | None = None,
    ) -> FormulaReviewRecord:
        self.get_formula_definition(formula_definition_id)
        record = FormulaReviewRecord(
            formula_definition_id=formula_definition_id,
            formula_evaluation_id=formula_evaluation_id,
            reviewer_id=reviewer_id,
            verdict=verdict,
            notes=notes,
            evidence_bundle=evidence_bundle or ReviewEvidenceBundle(),
        )
        return self.container.metadata.create_formula_review(record)

    def list_formula_reviews(self, formula_definition_id: str | None = None) -> list[FormulaReviewRecord]:
        return self.container.metadata.list_formula_reviews(formula_definition_id=formula_definition_id)

    def list_metric_definitions(self) -> list[MetricDefinition]:
        return self.container.metadata.list_metric_definitions()

    def list_metric_results(self, run_id: str | None = None) -> list[MetricResult]:
        return self.container.metadata.list_metric_results(run_id=run_id)

    def read_metrics(self, run_id: str) -> MetricReadResponse:
        metrics_asset = next((asset for asset in self.list_assets(run_id) if asset.kind.value == "metric_result"), None)
        return MetricReadResponse(
            run_id=run_id,
            metric_results=self.list_metric_results(run_id=run_id),
            metrics_asset=metrics_asset,
        )

    def compare_runs(self, left_run_id: str, right_run_id: str) -> dict[str, Any]:
        return self.container.metadata.compare_runs(left_run_id, right_run_id)

    def tool_create_session(self, title: str, dog_id: str | None = None, metadata: dict[str, Any] | None = None) -> ToolResponse:
        session = self.create_session(title=title, dog_id=dog_id, metadata=metadata)
        return ToolResponse(ok=True, resource_id=session.session_id, status="created", data=session.model_dump(mode="json"))

    def tool_list_sessions(self) -> ToolResponse:
        sessions = [item.model_dump(mode="json") for item in self.list_sessions()]
        return ToolResponse(ok=True, status="ok", data={"sessions": sessions})

    def tool_delete_session(self, session_id: str) -> ToolResponse:
        self.delete_session(session_id)
        return ToolResponse(ok=True, resource_id=session_id, status="deleted", data={"session_id": session_id})

    @staticmethod
    def _resolve_session_attachment_kind(*, file_name: str, mime_type: str) -> AssetKind:
        normalized_mime = mime_type.lower()
        suffix = Path(file_name).suffix.lower()
        if normalized_mime.startswith("video/") or suffix in {".mp4", ".mov", ".avi", ".webm", ".m4v", ".mkv"}:
            return AssetKind.VIDEO
        if normalized_mime.startswith("image/") or suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}:
            return AssetKind.IMAGE
        if normalized_mime.startswith("text/") or mime_type in {"application/json", "text/csv"} or suffix in {
            ".txt",
            ".md",
            ".csv",
            ".json",
            ".yaml",
            ".yml",
            ".log",
            ".xml",
        }:
            return AssetKind.TEXT
        raise ValueError(f"Unsupported attachment type: {mime_type or suffix or 'unknown'}")

    @staticmethod
    def _build_session_attachment_name(file_name: str) -> str:
        original = Path(file_name).name or "attachment"
        sanitized = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in original)
        return f"{uuid4()}-{sanitized.lstrip('-') or 'attachment'}"

    def tool_create_run(
        self,
        session_id: str,
        manifest: ExperimentManifest,
        execution_plan: ExecutionPlan | None = None,
        run_kind: RunKind = RunKind.PIPELINE,
    ) -> ToolResponse:
        run = self.create_run(session_id=session_id, manifest=manifest, execution_plan=execution_plan, run_kind=run_kind)
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

    def tool_read_metrics(self, run_id: str) -> ToolResponse:
        metrics = self.read_metrics(run_id)
        return ToolResponse(ok=True, resource_id=run_id, status="ok", data=metrics.model_dump(mode="json"))

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
        return ToolResponse(ok=True, status="ok", data={"filters": filters, "message": "Placeholder dataset search scaffold."})

    def tool_visualize_pysr_manifest(self, manifest: dict[str, Any]) -> ToolResponse:
        report = summarize_manifest(manifest)
        return ToolResponse(ok=True, status="ok", data=report)

    def respond_to_console(
        self,
        *,
        session_id: str,
        message: str,
        display_preferences: list[DisplayPreference] | None = None,
        active_context: ActiveContext | None = None,
    ) -> ConsoleAgentResponse:
        session = self.container.metadata.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id}")

        preferences = self._merge_display_preferences(message=message, explicit=display_preferences or [])
        console_state = self._build_console_state(session_id=session_id, message=message)
        modules = self._build_console_modules(
            session=session,
            message=message,
            preferences=preferences,
            active_context=active_context,
            console_state=console_state,
        )
        view_modes = self._collect_view_modes(preferences=preferences, modules=modules)
        assistant_message = self._assistant_message(message=message, console_state=console_state)
        thread = [
            ConsoleThreadMessage(role="user", content=message),
            ConsoleThreadMessage(
                role="assistant",
                content=assistant_message,
            ),
        ]
        evidence_context = self._build_evidence_context(console_state=console_state)
        warnings = []
        if console_state["mode"] == "preview":
            warnings.append("The execution plan is ready, but no uploaded video is attached to this session yet.")
        if DisplayPreference.RAW_VALUES_ONLY in preferences:
            warnings.append("Raw values preference suppresses interpretation-heavy modules where possible.")
        if console_state["mode"] == "executed":
            suggested_followups = [
                "Show this as a table only.",
                "Open the supporting video and evidence trail.",
                "Compare this run against the previous completed run.",
            ]
        else:
            suggested_followups = [
                "Upload a session video and run this analysis again.",
                "Show the planned execution stages as a table.",
                "Explain which tool stage will produce each artifact.",
            ]
        return ConsoleAgentResponse(
            thread=thread,
            message=assistant_message,
            modules=modules,
            view_modes=view_modes,
            tool_trace=self._build_tool_trace(message=message, preferences=preferences, console_state=console_state),
            evidence_context=evidence_context,
            warnings=warnings,
            suggested_followups=suggested_followups,
        )

    def tool_console_respond(
        self,
        *,
        session_id: str,
        message: str,
        display_preferences: list[DisplayPreference] | None = None,
        active_context: ActiveContext | None = None,
    ) -> ToolResponse:
        response = self.respond_to_console(
            session_id=session_id,
            message=message,
            display_preferences=display_preferences,
            active_context=active_context,
        )
        return ToolResponse(ok=True, status="ok", data=response.model_dump(mode="json"))

    def _require_run(self, run_id: str) -> RunRecord:
        run = self.container.metadata.get_run(run_id)
        if run is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        return run

    def _update_job_state(
        self,
        job: JobRecord,
        *,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> JobRecord:
        job.status = status
        job.updated_at = utc_now()
        if run_id is not None:
            job.run_id = run_id
        if result is not None:
            job.result = result
            job.error = None
        if error is not None:
            job.error = error
        return self.container.metadata.update_job(job)

    @staticmethod
    def _merge_display_preferences(message: str, explicit: list[DisplayPreference]) -> list[DisplayPreference]:
        preferences = list(explicit)
        lowered = message.lower()
        mapping = {
            "table only": DisplayPreference.TABLE_ONLY,
            "show as table": DisplayPreference.TABLE_ONLY,
            "raw values": DisplayPreference.RAW_VALUES_ONLY,
            "show raw": DisplayPreference.RAW_VALUES_ONLY,
            "chart": DisplayPreference.PREFER_CHART,
            "plot": DisplayPreference.PREFER_CHART,
            "video": DisplayPreference.PREFER_VIDEO,
            "evidence": DisplayPreference.EVIDENCE_FIRST,
        }
        for needle, preference in mapping.items():
            if needle in lowered and preference not in preferences:
                preferences.append(preference)
        return preferences

    @staticmethod
    def _select_view_modes(preferences: list[DisplayPreference]) -> list[ConsoleViewMode]:
        modes = [
            ConsoleViewMode.SUMMARY,
            ConsoleViewMode.CHART,
            ConsoleViewMode.TABLE,
            ConsoleViewMode.EVIDENCE,
            ConsoleViewMode.VIDEO,
            ConsoleViewMode.FORMULA,
        ]
        if DisplayPreference.TABLE_ONLY in preferences:
            return [ConsoleViewMode.TABLE, ConsoleViewMode.EVIDENCE]
        if DisplayPreference.EVIDENCE_FIRST in preferences:
            return [ConsoleViewMode.EVIDENCE, ConsoleViewMode.SUMMARY, ConsoleViewMode.CHART, ConsoleViewMode.TABLE]
        return modes

    @staticmethod
    def _collect_view_modes(
        preferences: list[DisplayPreference],
        modules: list[
            SummaryCardModule
            | TrendChartModule
            | MetricTableModule
            | EvidencePanelModule
            | FormulaExplanationModule
            | VideoPanelModule
            | ComparisonCardsModule
        ],
    ) -> list[ConsoleViewMode]:
        if DisplayPreference.TABLE_ONLY in preferences:
            return [ConsoleViewMode.TABLE, ConsoleViewMode.EVIDENCE]
        if DisplayPreference.EVIDENCE_FIRST in preferences:
            return [ConsoleViewMode.EVIDENCE, ConsoleViewMode.SUMMARY, ConsoleViewMode.CHART, ConsoleViewMode.TABLE]
        seen: set[ConsoleViewMode] = set()
        ordered: list[ConsoleViewMode] = []
        for module in modules:
            if module.view_mode in seen:
                continue
            seen.add(module.view_mode)
            ordered.append(module.view_mode)
        return ordered or [ConsoleViewMode.SUMMARY]

    def _build_console_state(self, *, session_id: str, message: str) -> dict[str, Any]:
        planner = self._build_console_planner()
        manifest = planner.plan(goal=message)
        execution_plan = planner.plan_execution(goal=message)
        videos = self.list_session_videos(session_id)
        if not videos:
            return {
                "mode": "preview",
                "goal": message,
                "manifest": manifest.model_dump(mode="json"),
                "execution_plan": execution_plan.model_dump(mode="json"),
                "run_status": "blocked_no_video",
                "recommendation": "The agent could not execute this request because the session has no uploaded video yet.",
                "video_asset_id": None,
                "run_detail": None,
                "comparison": None,
            }

        graph = self._build_console_graph(planner=planner)
        graph_state = graph.invoke(goal=message, session_id=session_id)
        run_detail = self.get_run_detail(graph_state["run_id"])
        comparison = self._build_console_comparison(session_id=session_id, current_run_id=run_detail.run.run_id)
        return {
            "mode": "executed",
            **graph_state,
            "run_detail": run_detail,
            "comparison": comparison,
        }

    def _build_console_graph(self, planner: Any) -> Any:
        from hound_forward.agent_system.graphs.research_graph import ResearchGraph
        from hound_forward.agent_system.tools.registry import ToolRegistry
        from hound_forward.worker.runtime import InlineRunMonitor, PollingRunMonitor

        run_monitor = InlineRunMonitor(service=self) if PlatformSettings().placeholder_worker_mode else PollingRunMonitor(service=self)

        return ResearchGraph(
            planner=planner,
            tools=ToolRegistry(self),
            run_monitor=run_monitor,
        )

    def _build_console_planner(self) -> Any:
        from hound_forward.agent_system.planners import build_planner
        from hound_forward.settings import PlatformSettings

        settings = PlatformSettings()
        available_tools = self.container.tool_runner.describe_tools() if self.container.tool_runner else []
        return build_planner(settings=settings, available_tools=available_tools)

    def _build_console_comparison(self, *, session_id: str, current_run_id: str) -> dict[str, Any] | None:
        prior_runs = [
            run
            for run in self.list_runs(session_id=session_id)
            if run.run_id != current_run_id and run.status == RunStatus.COMPLETED
        ]
        if not prior_runs:
            return None
        baseline = sorted(prior_runs, key=lambda item: item.created_at)[-1]
        return self.compare_runs(baseline.run_id, current_run_id)

    def _build_console_modules(
        self,
        *,
        session: SessionRecord,
        message: str,
        preferences: list[DisplayPreference],
        active_context: ActiveContext | None,
        console_state: dict[str, Any],
    ) -> list[
        SummaryCardModule
        | TrendChartModule
        | MetricTableModule
        | EvidencePanelModule
        | FormulaExplanationModule
        | VideoPanelModule
        | ComparisonCardsModule
    ]:
        metric_name = active_context.metric_name if active_context and active_context.metric_name else "mobility_index_v2"
        run_detail: RunDetailResponse | None = console_state.get("run_detail")
        metrics = run_detail.metrics if run_detail is not None else []
        metric_map = {item.name: item.value for item in metrics}
        if run_detail is not None and run_detail.run.execution_plan is not None:
            stage_names = [stage.name for stage in run_detail.run.execution_plan.stages]
        else:
            stage_names = [stage.get("name", "unknown_stage") for stage in console_state.get("execution_plan", {}).get("stages", [])]
        report_summary = (
            run_detail.run.summary.get("last_stage_summary", {}) if run_detail is not None else {}
        )
        recommendations = report_summary.get("recommendations") or [console_state["recommendation"]]
        video_asset_id = (
            active_context.asset_id
            if active_context and active_context.asset_id
            else console_state.get("video_asset_id")
            or (run_detail.run.input_asset_ids[0] if run_detail is not None and run_detail.run.input_asset_ids else "video-unavailable")
        )
        summary_module = SummaryCardModule(
            title="Research Summary",
            payload=SummaryCardPayload(
                title="Execution summary" if run_detail is not None else "Execution plan preview",
                summary=recommendations[0],
                status="completed" if run_detail is not None else "blocked",
                highlights=[
                    HighlightItem(label="Dog", value=session.title),
                    HighlightItem(label="Goal", value=(run_detail.run.manifest.goal if run_detail is not None else message)[:72]),
                    HighlightItem(label="Stages", value=str(len(stage_names))),
                    HighlightItem(
                        label="Run status",
                        value=run_detail.run.status.value if run_detail is not None else "waiting_for_video",
                    ),
                ],
            ),
        )
        trend_module = TrendChartModule(
            title="Trend Chart",
            payload=TrendChartPayload(
                metric=metric_name if metrics else "planned_execution_stages",
                unit="score" if metrics else "stage",
                time_range="current run" if metrics else "pre-run",
                x_axis="Metric" if metrics else "Stage",
                y_axis="Value" if metrics else "Sequence",
                series=[
                    {"label": name, "value": round(value, 4)}
                    for name, value in sorted(metric_map.items())
                ]
                if metrics
                else [
                    {"label": stage_name, "value": float(index + 1)}
                    for index, stage_name in enumerate(stage_names)
                ],
            ),
        )
        table_module = MetricTableModule(
            title="Metric Table",
            payload=MetricTablePayload(
                metric=metric_name if metrics else "execution_plan",
                columns=(
                    [
                        MetricTableColumn(key="metric", label="Metric"),
                        MetricTableColumn(key="value", label="Value"),
                        MetricTableColumn(key="version", label="Version"),
                    ]
                    if metrics
                    else [
                        MetricTableColumn(key="stage", label="Stage"),
                        MetricTableColumn(key="tool", label="Tool"),
                        MetricTableColumn(key="status", label="Status"),
                    ]
                ),
                rows=(
                    [
                        MetricTableRow(
                            values={"metric": item.name, "value": round(item.value, 4), "version": item.version},
                            raw=DisplayPreference.RAW_VALUES_ONLY in preferences,
                            derived=True,
                        )
                        for item in metrics
                    ]
                    if metrics
                    else [
                        MetricTableRow(
                            values={
                                "stage": stage.get("name", "unknown_stage"),
                                "tool": (stage.get("tool_invocation") or {}).get("tool_name", "n/a"),
                                "status": "planned",
                            },
                            raw=False,
                            derived=False,
                        )
                        for stage in console_state.get("execution_plan", {}).get("stages", [])
                    ]
                ),
                sort="metric.asc" if metrics else "stage.asc",
            ),
        )
        evidence_module = EvidencePanelModule(
            title="Evidence Panel",
            payload=EvidencePanelPayload(
                confidence="moderate" if run_detail is not None else "not_available",
                review_status="run_completed" if run_detail is not None else "awaiting_input_video",
                missingness=(
                    "No missing metric artifacts were detected in this run."
                    if run_detail is not None
                    else "The agent has not run yet because this session has no uploaded video."
                ),
                provenance=(
                    f"Run {run_detail.run.run_id} executed {len(stage_names)} planned tool stages."
                    if run_detail is not None
                    else f"Planned execution chain: {' -> '.join(stage_names)}."
                ),
                sources=[
                    {"label": "Run", "kind": "run", "reference": run_detail.run.run_id if run_detail is not None else "pending"},
                    {"label": "Plan", "kind": "execution_plan", "reference": console_state.get("execution_plan", {}).get("plan_id", "unknown-plan")},
                    {"label": "Video", "kind": "video", "reference": video_asset_id},
                ],
            ),
        )
        video_module = VideoPanelModule(
            title="Video Review",
            payload=VideoPanelPayload(
                asset_id=video_asset_id,
                title="Session analysis input",
                timestamp_range="full clip",
                related_metrics=sorted(metric_map.keys()) if metric_map else [metric_name],
            ),
        )
        comparison = console_state.get("comparison")
        comparison_module = ComparisonCardsModule(
            title="Comparison Cards",
            payload=ComparisonCardsPayload(
                title="Run-over-run comparison",
                items=[
                    ComparisonCardItem(
                        label=item["name"],
                        value="n/a" if item["right"] is None else f'{item["right"]:.4f}',
                        delta=(
                            None
                            if item["delta"] is None
                            else f'{item["delta"]:+.4f}'
                        ),
                    )
                    for item in (comparison or {}).get("metrics", [])[:4]
                ],
            ),
        )

        modules: list[Any] = [summary_module, trend_module, table_module, evidence_module]
        if run_detail is not None:
            modules.append(video_module)
        if comparison and comparison_module.payload.items:
            modules.append(comparison_module)
        if DisplayPreference.TABLE_ONLY in preferences:
            return [table_module, evidence_module]
        if DisplayPreference.RAW_VALUES_ONLY in preferences:
            raw_modules: list[Any] = [summary_module, table_module, evidence_module]
            if run_detail is not None:
                raw_modules.append(video_module)
            return raw_modules
        if DisplayPreference.PREFER_VIDEO in preferences and run_detail is not None:
            return [summary_module, video_module, trend_module, evidence_module]
        if DisplayPreference.EVIDENCE_FIRST in preferences:
            ordered = [evidence_module, summary_module, trend_module, table_module]
            if run_detail is not None:
                ordered.append(video_module)
            if comparison and comparison_module.payload.items:
                ordered.append(comparison_module)
            return ordered
        if "compare" in message.lower() and comparison and comparison_module.payload.items:
            return [summary_module, comparison_module, trend_module, table_module, evidence_module]
        return modules

    @staticmethod
    def _build_tool_trace(
        message: str,
        preferences: list[DisplayPreference],
        console_state: dict[str, Any],
    ) -> list[ToolTraceItem]:
        execution_plan = console_state.get("execution_plan", {})
        stages = execution_plan.get("stages", [])
        trace = [
            ToolTraceItem(
                tool_name="intent_parser",
                purpose="Normalize user goal and display intent into console semantics.",
                status="ok",
                details={"message": message, "display_preferences": [item.value for item in preferences]},
            ),
            ToolTraceItem(
                tool_name="planner",
                purpose="Build a LangGraph manifest and execution plan for the console request.",
                status="ok",
                details={"stage_names": [stage.get("name") for stage in stages], "plan_id": execution_plan.get("plan_id")},
            ),
        ]
        if console_state.get("mode") == "executed":
            run_detail: RunDetailResponse = console_state["run_detail"]
            trace.extend(
                [
                    ToolTraceItem(
                        tool_name="langgraph_execute",
                        purpose="Execute the planned tool chain against the session video.",
                        status=run_detail.run.status.value,
                        details={"run_id": run_detail.run.run_id, "stage_count": len(run_detail.run.stage_results)},
                    ),
                    ToolTraceItem(
                        tool_name="read_metrics",
                        purpose="Collect metric outputs and report recommendations from the finished run.",
                        status="ok",
                        details={"metric_names": [item.name for item in run_detail.metrics]},
                    ),
                ]
            )
        else:
            trace.append(
                ToolTraceItem(
                    tool_name="execution_blocker",
                    purpose="Explain why the planned execution chain did not run.",
                    status="blocked",
                    details={"reason": "missing_session_video"},
                )
            )
        return trace

    @staticmethod
    def _assistant_message(message: str, console_state: dict[str, Any]) -> str:
        if console_state.get("mode") != "executed":
            stage_names = [stage.get("name") for stage in console_state.get("execution_plan", {}).get("stages", [])]
            return (
                f'I planned the tool chain for "{message}"'
                f" ({' -> '.join(stage_names)}), but this session has no uploaded video, so the analysis could not run yet."
            )

        run_detail: RunDetailResponse = console_state["run_detail"]
        metrics = {item.name: item.value for item in run_detail.metrics}
        metric_fragments = [f"{name}={value:.4f}" for name, value in sorted(metrics.items())]
        recommendation = console_state.get("recommendation") or run_detail.run.summary.get("last_stage_summary", {}).get("recommendations", [""])[0]
        return (
            f'I ran {len(run_detail.run.stage_results)} stages for "{message}"'
            f" on run {run_detail.run.run_id}. "
            f"Observed metrics: {', '.join(metric_fragments) if metric_fragments else 'no metric outputs were produced'}. "
            f"{recommendation}"
        )

    @staticmethod
    def _build_evidence_context(console_state: dict[str, Any]) -> EvidenceContext:
        if console_state.get("mode") == "executed":
            run_detail: RunDetailResponse = console_state["run_detail"]
            metric_names = [item.name for item in run_detail.metrics]
            return EvidenceContext(
                metric_definition=", ".join(metric_names) if metric_names else "no_metrics",
                time_range="current run",
                data_quality="Metrics were produced by the executed LangGraph tool chain.",
                clinician_reviewed=False,
                derived_metric=bool(metric_names),
                references=[
                    run_detail.run.run_id,
                    run_detail.run.execution_plan.plan_id if run_detail.run.execution_plan is not None else "unknown-plan",
                    *(run_detail.run.input_asset_ids[:1]),
                ],
            )

        execution_plan = console_state.get("execution_plan", {})
        return EvidenceContext(
            metric_definition="execution_plan_preview",
            time_range="pre-run",
            data_quality="No run output is available because the session has no uploaded video.",
            clinician_reviewed=False,
            derived_metric=False,
            references=[
                execution_plan.get("plan_id", "unknown-plan"),
                *(stage.get("name", "unknown_stage") for stage in execution_plan.get("stages", [])),
            ],
        )

    def _find_next_queued_run(self) -> RunRecord | None:
        for run in self.container.metadata.list_runs():
            if run.status == RunStatus.QUEUED:
                return run
        return None

    @staticmethod
    def _build_default_execution_plan(run_kind: RunKind, manifest: ExperimentManifest) -> ExecutionPlan:
        stages = [
            ExecutionStage(
                name="extract_keypoints",
                stage_type=ExecutionStageType.AGENT_TOOL,
                tool_invocation=ToolInvocationRecord(
                    tool_name="extract_keypoints",
                    input_asset_id=manifest.input_asset_ids[0] if manifest.input_asset_ids else None,
                ),
                metadata={"planned_by": "service_default", "run_kind": run_kind.value},
            ),
            ExecutionStage(
                name="compute_gait_metrics",
                stage_type=ExecutionStageType.AGENT_TOOL,
                tool_invocation=ToolInvocationRecord(tool_name="compute_gait_metrics"),
                metadata={"planned_by": "service_default", "run_kind": run_kind.value},
            ),
            ExecutionStage(
                name="generate_report",
                stage_type=ExecutionStageType.AGENT_TOOL,
                tool_invocation=ToolInvocationRecord(tool_name="generate_report"),
                metadata={"planned_by": "service_default", "run_kind": run_kind.value},
            ),
        ]
        if run_kind == RunKind.FORMULA_EVALUATION:
            stages.insert(
                0,
                ExecutionStage(
                    name="decode_video",
                    stage_type=ExecutionStageType.AGENT_TOOL,
                    tool_invocation=ToolInvocationRecord(
                        tool_name="decode_video",
                        input_asset_id=manifest.input_asset_ids[0] if manifest.input_asset_ids else None,
                    ),
                    metadata={"planned_by": "service_default", "run_kind": run_kind.value},
                ),
            )
        return ExecutionPlan(stages=stages)

    @staticmethod
    def _build_stage_results(run: RunRecord, assets: list[AssetRecord], summary: dict[str, Any]) -> list[StageResult]:
        asset_ids = [asset.asset_id for asset in assets]
        if not run.execution_plan:
            return []
        stage_results: list[StageResult] = []
        for index, stage in enumerate(run.execution_plan.stages):
            produced = asset_ids if index == len(run.execution_plan.stages) - 1 else []
            stage_results.append(
                StageResult(
                    stage_id=stage.stage_id,
                    name=stage.name,
                    status=RunStatus.COMPLETED,
                    produced_asset_ids=produced,
                    summary={"run_id": run.run_id, **summary},
                )
            )
        return stage_results
