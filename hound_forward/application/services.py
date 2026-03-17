from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from hound_forward.agent_tools import summarize_manifest

from hound_forward.domain import (
    ActiveContext,
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
    SummaryCardModule,
    SummaryCardPayload,
    StageResult,
    ToolTraceItem,
    ToolInvocationRecord,
    ToolResponse,
    TrendChartModule,
    TrendChartPayload,
    VideoUploadResponse,
    VideoPanelModule,
    VideoPanelPayload,
)
from hound_forward.ports import ArtifactStore, Job, JobQueue, MetadataRepository, RunExecutor, ToolRunner


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ServiceContainer:
    metadata: MetadataRepository
    artifact_store: ArtifactStore
    queue: JobQueue
    executor: RunExecutor
    tool_runner: ToolRunner | None = None


class ResearchPlatformService:
    """Application boundary for sessions, runs, assets, metrics, and agent tools."""

    def __init__(self, container: ServiceContainer) -> None:
        self.container = container

    def create_session(self, title: str, dog_id: str | None = None, metadata: dict[str, Any] | None = None) -> SessionRecord:
        session = SessionRecord(title=title, dog_id=dog_id, metadata=metadata or {})
        return self.container.metadata.create_session(session)

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

    def upload_session_video(
        self,
        *,
        session_id: str,
        file_name: str,
        content: bytes,
        mime_type: str = "video/mp4",
    ) -> VideoUploadResponse:
        session = self.container.metadata.get_session(session_id)
        if session is None:
            raise KeyError(f"Unknown session_id: {session_id}")
        asset = self.container.artifact_store.put_bytes(
            session_id=session_id,
            name=file_name,
            content=content,
            kind="video",
            mime_type=mime_type,
            metadata={
                "placeholder_flags": {"dummy": True, "fake": False, "placeholder": True},
                "runtime_validation": True,
            },
        )
        registered = self.container.metadata.register_asset(asset)
        return VideoUploadResponse(session_id=session_id, asset=registered)

    def list_session_videos(self, session_id: str) -> list[AssetRecord]:
        return self.container.metadata.list_session_assets(session_id=session_id, kind="video")

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
        if job is not None:
            run = self._require_run(job.run_id)
        else:
            run = self._find_next_queued_run()
            if run is None:
                return None
        run.status = RunStatus.RUNNING
        run.updated_at = utc_now()
        self.container.metadata.update_run(run)
        self.container.metadata.append_run_event(RunEvent(run_id=run.run_id, status=RunStatus.RUNNING, message="Run started."))
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
        view_modes = self._select_view_modes(preferences)
        modules = self._build_console_modules(session=session, message=message, preferences=preferences, active_context=active_context)
        thread = [
            ConsoleThreadMessage(role="user", content=message),
            ConsoleThreadMessage(
                role="assistant",
                content="Research console response assembled from controlled visual modules and evidence-aware summaries.",
            ),
        ]
        evidence_context = EvidenceContext(
            metric_definition="mobility_index_v2",
            time_range="Last 6 months",
            data_quality="2 sessions contain incomplete metadata; values are still suitable for trend review.",
            clinician_reviewed=True,
            derived_metric=True,
            references=["run-001", "formula:mobility_index_v2", "video:video-001"],
        )
        warnings = []
        if DisplayPreference.RAW_VALUES_ONLY in preferences:
            warnings.append("Raw values preference suppresses interpretation-heavy modules where possible.")
        suggested_followups = [
            "Show this as a table only.",
            "Open the supporting video and evidence trail.",
            "Compare this against the clinician validation cohort.",
        ]
        return ConsoleAgentResponse(
            thread=thread,
            message=self._assistant_message(message=message, preferences=preferences),
            modules=modules,
            view_modes=view_modes,
            tool_trace=self._build_tool_trace(message=message, preferences=preferences),
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

    def _build_console_modules(
        self,
        *,
        session: SessionRecord,
        message: str,
        preferences: list[DisplayPreference],
        active_context: ActiveContext | None,
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
        summary_module = SummaryCardModule(
            title="Research Summary",
            payload=SummaryCardPayload(
                title="Mobility trend review",
                summary="Mobility has softened through March, with the sharpest deviation aligned to reduced stride symmetry.",
                status="attention_needed",
                highlights=[
                    HighlightItem(label="Dog", value=session.title),
                    HighlightItem(label="Focus metric", value=metric_name),
                    HighlightItem(label="Abnormal window", value="March"),
                ],
            ),
        )
        trend_module = TrendChartModule(
            title="Trend Chart",
            payload=TrendChartPayload(
                metric=metric_name,
                unit="score",
                time_range="12 months",
                x_axis="Month",
                y_axis="Mobility score",
                series=[
                    {"label": "Jan", "value": 0.82},
                    {"label": "Feb", "value": 0.8},
                    {"label": "Mar", "value": 0.61},
                    {"label": "Apr", "value": 0.66},
                    {"label": "May", "value": 0.71},
                    {"label": "Jun", "value": 0.74},
                ],
            ),
        )
        table_module = MetricTableModule(
            title="Metric Table",
            payload=MetricTablePayload(
                metric=metric_name,
                columns=[
                    MetricTableColumn(key="month", label="Month"),
                    MetricTableColumn(key="value", label="Value"),
                    MetricTableColumn(key="quality", label="Quality"),
                ],
                rows=[
                    MetricTableRow(values={"month": "Jan", "value": 0.82, "quality": "complete"}, raw=False, derived=True),
                    MetricTableRow(values={"month": "Feb", "value": 0.80, "quality": "complete"}, raw=False, derived=True),
                    MetricTableRow(values={"month": "Mar", "value": 0.61, "quality": "missing metadata"}, raw=False, derived=True),
                ],
                sort="month.asc",
            ),
        )
        evidence_module = EvidencePanelModule(
            title="Evidence Panel",
            payload=EvidencePanelPayload(
                confidence="moderate",
                review_status="clinician_reviewed",
                missingness="2 of 14 sessions have incomplete metadata.",
                provenance="Derived from stride_length / body_length with March anomaly evidence linked to asymmetry drift.",
                sources=[
                    {"label": "Run", "kind": "run", "reference": "run-001"},
                    {"label": "Formula", "kind": "formula", "reference": "mobility_index_v2"},
                    {"label": "Video", "kind": "video", "reference": active_context.asset_id if active_context and active_context.asset_id else "video-001"},
                ],
            ),
        )
        formula_module = FormulaExplanationModule(
            title="Formula Explanation",
            payload=FormulaExplanationPayload(
                formula_id="mobility_index_v2",
                expression="stride_length / body_length",
                interpretation="Normalizing stride length by body size allows locomotion efficiency to be compared across dogs of different sizes.",
                assumptions=[
                    "Body length normalization remains stable across the observation window.",
                    "Stride extraction quality is sufficient for month-level comparison.",
                ],
            ),
        )
        video_module = VideoPanelModule(
            title="Video Review",
            payload=VideoPanelPayload(
                asset_id=active_context.asset_id if active_context and active_context.asset_id else "video-001",
                title="March gait review clip",
                timestamp_range="00:12-00:26",
                related_metrics=[metric_name, "asymmetry_index"],
            ),
        )
        comparison_module = ComparisonCardsModule(
            title="Comparison Cards",
            payload=ComparisonCardsPayload(
                title="Month-over-month comparison",
                items=[
                    ComparisonCardItem(label="March vs February", value="-0.19", delta="-24%"),
                    ComparisonCardItem(label="March asymmetry", value="0.18", delta="+0.07"),
                ],
            ),
        )

        modules: list[Any] = [summary_module, trend_module, table_module, evidence_module, formula_module, video_module, comparison_module]
        if DisplayPreference.TABLE_ONLY in preferences:
            return [table_module, evidence_module]
        if DisplayPreference.RAW_VALUES_ONLY in preferences:
            return [summary_module, table_module, evidence_module]
        if DisplayPreference.PREFER_VIDEO in preferences:
            return [summary_module, video_module, trend_module, evidence_module, formula_module]
        if DisplayPreference.EVIDENCE_FIRST in preferences:
            return [evidence_module, summary_module, trend_module, table_module, formula_module]
        if "compare" in message.lower():
            return [summary_module, comparison_module, trend_module, table_module, evidence_module]
        return modules

    @staticmethod
    def _build_tool_trace(message: str, preferences: list[DisplayPreference]) -> list[ToolTraceItem]:
        return [
            ToolTraceItem(
                tool_name="intent_parser",
                purpose="Normalize user goal and display intent into console semantics.",
                status="ok",
                details={"message": message, "display_preferences": [item.value for item in preferences]},
            ),
            ToolTraceItem(
                tool_name="read_metrics",
                purpose="Retrieve placeholder metric evidence for the selected session context.",
                status="ok",
                details={"metric": "mobility_index_v2", "time_range": "12 months"},
            ),
            ToolTraceItem(
                tool_name="render_modules",
                purpose="Select controlled visual modules for frontend rendering.",
                status="ok",
                details={"module_types": ["summary_card", "trend_chart", "metric_table", "evidence_panel"]},
            ),
        ]

    @staticmethod
    def _assistant_message(message: str, preferences: list[DisplayPreference]) -> str:
        if DisplayPreference.TABLE_ONLY in preferences:
            return "The trend has been reduced to a table-first view with supporting evidence because you requested a table-oriented output."
        if DisplayPreference.PREFER_VIDEO in preferences:
            return "The response prioritizes video review because your prompt indicates you want supporting visual session evidence."
        if "compare" in message.lower():
            return "The console assembled a comparison-focused response using controlled cards, trend evidence, and a supporting metric table."
        return "The console assembled a summary, chart, table, evidence, video, and formula explanation using controlled visual modules."

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
