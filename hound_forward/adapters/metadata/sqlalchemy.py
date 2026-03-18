from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, DateTime, Float, String, create_engine, delete, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from hound_forward.domain import (
    AssetKind,
    AssetRecord,
    ExperimentManifest,
    ExecutionPlan,
    FormulaDefinitionRecord,
    FormulaEvaluationRecord,
    FormulaProposalRecord,
    FormulaReviewRecord,
    FormulaStatus,
    JobRecord,
    JobStatus,
    JobType,
    MetricDefinition,
    MetricResult,
    ReviewEvidenceBundle,
    ReviewVerdict,
    RunEvent,
    RunKind,
    RunRecord,
    RunStatus,
    SessionRecord,
    StageResult,
)


class Base(DeclarativeBase):
    pass


class SessionModel(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    dog_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RunModel(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    run_kind: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    manifest_json: Mapped[dict[str, Any]] = mapped_column("manifest", JSON)
    input_asset_ids_json: Mapped[list[str]] = mapped_column("input_asset_ids", JSON, default=list)
    execution_plan_json: Mapped[dict[str, Any] | None] = mapped_column("execution_plan", JSON, nullable=True)
    stage_results_json: Mapped[list[dict[str, Any]]] = mapped_column("stage_results", JSON, default=list)
    summary_json: Mapped[dict[str, Any]] = mapped_column("summary", JSON, default=dict)
    error_json: Mapped[dict[str, Any] | None] = mapped_column("error", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RunEventModel(Base):
    __tablename__ = "run_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    payload_json: Mapped[dict[str, Any]] = mapped_column("payload", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class JobModel(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    job_type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    session_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    run_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column("payload", JSON, default=dict)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    result_json: Mapped[dict[str, Any] | None] = mapped_column("result", JSON, nullable=True)
    error_json: Mapped[dict[str, Any] | None] = mapped_column("error", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AssetModel(Base):
    __tablename__ = "assets"

    asset_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    kind: Mapped[str] = mapped_column(String, index=True)
    blob_path: Mapped[str] = mapped_column(String)
    checksum: Mapped[str] = mapped_column(String)
    mime_type: Mapped[str] = mapped_column(String)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MetricDefinitionModel(Base):
    __tablename__ = "metric_definitions"

    metric_definition_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    config_schema_json: Mapped[dict[str, Any]] = mapped_column("config_schema", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MetricResultModel(Base):
    __tablename__ = "metric_results"

    metric_result_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    metric_definition_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float)
    payload_json: Mapped[dict[str, Any]] = mapped_column("payload", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FormulaDefinitionModel(Base):
    __tablename__ = "formula_definitions"

    formula_definition_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    input_requirements_json: Mapped[dict[str, Any]] = mapped_column("input_requirements", JSON, default=dict)
    execution_spec_json: Mapped[dict[str, Any]] = mapped_column("execution_spec", JSON, default=dict)
    provenance_json: Mapped[dict[str, Any]] = mapped_column("provenance", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FormulaProposalModel(Base):
    __tablename__ = "formula_proposals"

    formula_proposal_id: Mapped[str] = mapped_column(String, primary_key=True)
    formula_definition_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    source_run_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    research_question: Mapped[str] = mapped_column(String)
    proposal_payload_json: Mapped[dict[str, Any]] = mapped_column("proposal_payload", JSON, default=dict)
    provenance_json: Mapped[dict[str, Any]] = mapped_column("provenance", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FormulaEvaluationModel(Base):
    __tablename__ = "formula_evaluations"

    formula_evaluation_id: Mapped[str] = mapped_column(String, primary_key=True)
    formula_definition_id: Mapped[str] = mapped_column(String, index=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    dataset_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    summary_json: Mapped[dict[str, Any]] = mapped_column("summary", JSON, default=dict)
    provenance_json: Mapped[dict[str, Any]] = mapped_column("provenance", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FormulaReviewModel(Base):
    __tablename__ = "formula_reviews"

    formula_review_id: Mapped[str] = mapped_column(String, primary_key=True)
    formula_definition_id: Mapped[str] = mapped_column(String, index=True)
    formula_evaluation_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    reviewer_id: Mapped[str] = mapped_column(String)
    verdict: Mapped[str] = mapped_column(String, index=True)
    notes: Mapped[str] = mapped_column(String)
    evidence_bundle_json: Mapped[dict[str, Any]] = mapped_column("evidence_bundle", JSON, default=dict)
    provenance_json: Mapped[dict[str, Any]] = mapped_column("provenance", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemyMetadataRepository:
    """Metadata repository backed by SQLAlchemy-compatible PostgreSQL or SQLite."""

    def __init__(self, database_url: str) -> None:
        engine_kwargs: dict[str, Any] = {"future": True}
        if database_url.startswith("sqlite"):
            self._ensure_sqlite_parent_dir(database_url)
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            if database_url.endswith(":memory:"):
                engine_kwargs["poolclass"] = StaticPool
        self.engine = create_engine(database_url, **engine_kwargs)
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False, class_=Session)

    def create_all(self) -> None:
        Base.metadata.create_all(self.engine)
        self._ensure_local_runtime_validation_columns()

    def create_session(self, session: SessionRecord) -> SessionRecord:
        with self._session_factory.begin() as db:
            db.add(
                SessionModel(
                    session_id=session.session_id,
                    dog_id=session.dog_id,
                    title=session.title,
                    status=session.status,
                    metadata_json=session.metadata,
                    created_at=session.created_at,
                )
            )
        return session

    def get_session(self, session_id: str) -> SessionRecord | None:
        with self._session_factory() as db:
            model = db.get(SessionModel, session_id)
            if model is None:
                return None
            return SessionRecord(
                session_id=model.session_id,
                dog_id=model.dog_id,
                title=model.title,
                status=model.status,
                metadata=model.metadata_json,
                created_at=model.created_at,
            )

    def list_sessions(self) -> list[SessionRecord]:
        with self._session_factory() as db:
            stmt = select(SessionModel).order_by(SessionModel.created_at.desc())
            return [
                SessionRecord(
                    session_id=model.session_id,
                    dog_id=model.dog_id,
                    title=model.title,
                    status=model.status,
                    metadata=model.metadata_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    def delete_session(self, session_id: str) -> bool:
        with self._session_factory.begin() as db:
            session_model = db.get(SessionModel, session_id)
            if session_model is None:
                return False

            run_ids = list(db.scalars(select(RunModel.run_id).where(RunModel.session_id == session_id)))
            if run_ids:
                formula_evaluation_ids = list(
                    db.scalars(select(FormulaEvaluationModel.formula_evaluation_id).where(FormulaEvaluationModel.run_id.in_(run_ids)))
                )
                if formula_evaluation_ids:
                    db.execute(
                        delete(FormulaReviewModel).where(FormulaReviewModel.formula_evaluation_id.in_(formula_evaluation_ids))
                    )
                db.execute(delete(FormulaEvaluationModel).where(FormulaEvaluationModel.run_id.in_(run_ids)))
                db.execute(delete(FormulaProposalModel).where(FormulaProposalModel.source_run_id.in_(run_ids)))
                db.execute(delete(MetricResultModel).where(MetricResultModel.run_id.in_(run_ids)))
                db.execute(delete(RunEventModel).where(RunEventModel.run_id.in_(run_ids)))
                db.execute(delete(JobModel).where(JobModel.run_id.in_(run_ids)))
                db.execute(delete(AssetModel).where(AssetModel.run_id.in_(run_ids)))
                db.execute(delete(RunModel).where(RunModel.run_id.in_(run_ids)))

            db.execute(delete(JobModel).where(JobModel.session_id == session_id))
            db.execute(delete(AssetModel).where(AssetModel.session_id == session_id))
            db.delete(session_model)
        return True

    def create_run(self, run: RunRecord) -> RunRecord:
        with self._session_factory.begin() as db:
            db.add(self._run_model(run))
        return run

    def update_run(self, run: RunRecord) -> RunRecord:
        with self._session_factory.begin() as db:
            model = db.get(RunModel, run.run_id)
            if model is None:
                raise KeyError(f"Unknown run_id: {run.run_id}")
            self._write_run_model(model, run)
        return run

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._session_factory() as db:
            model = db.get(RunModel, run_id)
            return None if model is None else self._read_run_model(model)

    def list_runs(self, session_id: str | None = None) -> list[RunRecord]:
        with self._session_factory() as db:
            stmt = select(RunModel).order_by(RunModel.created_at.desc())
            if session_id is not None:
                stmt = stmt.where(RunModel.session_id == session_id)
            return [self._read_run_model(model) for model in db.scalars(stmt)]

    def create_job(self, job: JobRecord) -> JobRecord:
        with self._session_factory.begin() as db:
            db.add(self._job_model(job))
        return job

    def update_job(self, job: JobRecord) -> JobRecord:
        with self._session_factory.begin() as db:
            model = db.get(JobModel, job.job_id)
            if model is None:
                raise KeyError(f"Unknown job_id: {job.job_id}")
            self._write_job_model(model, job)
        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._session_factory() as db:
            model = db.get(JobModel, job_id)
            return None if model is None else self._read_job_model(model)

    def list_jobs(
        self,
        *,
        session_id: str | None = None,
        run_id: str | None = None,
        job_type: str | None = None,
    ) -> list[JobRecord]:
        with self._session_factory() as db:
            stmt = select(JobModel).order_by(JobModel.created_at.desc())
            if session_id is not None:
                stmt = stmt.where(JobModel.session_id == session_id)
            if run_id is not None:
                stmt = stmt.where(JobModel.run_id == run_id)
            if job_type is not None:
                stmt = stmt.where(JobModel.job_type == job_type)
            return [self._read_job_model(model) for model in db.scalars(stmt)]

    def get_asset(self, asset_id: str) -> AssetRecord | None:
        with self._session_factory() as db:
            model = db.get(AssetModel, asset_id)
            return None if model is None else self._read_asset_model(model)

    def append_run_event(self, event: RunEvent) -> RunEvent:
        with self._session_factory.begin() as db:
            db.add(
                RunEventModel(
                    event_id=event.event_id,
                    run_id=event.run_id,
                    status=event.status.value,
                    message=event.message,
                    payload_json=event.payload,
                    created_at=event.created_at,
                )
            )
        return event

    def list_run_events(self, run_id: str) -> list[RunEvent]:
        with self._session_factory() as db:
            stmt = select(RunEventModel).where(RunEventModel.run_id == run_id).order_by(RunEventModel.created_at.asc())
            return [
                RunEvent(
                    event_id=model.event_id,
                    run_id=model.run_id,
                    status=RunStatus(model.status),
                    message=model.message,
                    payload=model.payload_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    def register_asset(self, asset: AssetRecord) -> AssetRecord:
        with self._session_factory.begin() as db:
            existing = db.get(AssetModel, asset.asset_id)
            if existing is None:
                db.add(self._asset_model(asset))
            else:
                self._write_asset_model(existing, asset)
        return asset

    def list_assets(self, run_id: str) -> list[AssetRecord]:
        with self._session_factory() as db:
            stmt = select(AssetModel).where(AssetModel.run_id == run_id).order_by(AssetModel.created_at.asc())
            return [self._read_asset_model(model) for model in db.scalars(stmt)]

    def list_session_assets(self, session_id: str, kind: str | None = None) -> list[AssetRecord]:
        with self._session_factory() as db:
            stmt = select(AssetModel).where(AssetModel.session_id == session_id).order_by(AssetModel.created_at.desc())
            if kind is not None:
                stmt = stmt.where(AssetModel.kind == kind)
            return [self._read_asset_model(model) for model in db.scalars(stmt)]

    def register_metric_definition(self, metric_definition: MetricDefinition) -> MetricDefinition:
        with self._session_factory.begin() as db:
            existing = db.get(MetricDefinitionModel, metric_definition.metric_definition_id)
            if existing is None:
                db.add(
                    MetricDefinitionModel(
                        metric_definition_id=metric_definition.metric_definition_id,
                        name=metric_definition.name,
                        version=metric_definition.version,
                        description=metric_definition.description,
                        config_schema_json=metric_definition.config_schema,
                        created_at=metric_definition.created_at,
                    )
                )
            else:
                existing.name = metric_definition.name
                existing.version = metric_definition.version
                existing.description = metric_definition.description
                existing.config_schema_json = metric_definition.config_schema
        return metric_definition

    def list_metric_definitions(self) -> list[MetricDefinition]:
        with self._session_factory() as db:
            stmt = select(MetricDefinitionModel).order_by(MetricDefinitionModel.name.asc(), MetricDefinitionModel.version.asc())
            return [
                MetricDefinition(
                    metric_definition_id=model.metric_definition_id,
                    name=model.name,
                    version=model.version,
                    description=model.description,
                    config_schema=model.config_schema_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    def register_metric_result(self, metric_result: MetricResult) -> MetricResult:
        with self._session_factory.begin() as db:
            existing = db.get(MetricResultModel, metric_result.metric_result_id)
            if existing is None:
                db.add(
                    MetricResultModel(
                        metric_result_id=metric_result.metric_result_id,
                        run_id=metric_result.run_id,
                        metric_definition_id=metric_result.metric_definition_id,
                        name=metric_result.name,
                        version=metric_result.version,
                        value=metric_result.value,
                        payload_json=metric_result.payload,
                        created_at=metric_result.created_at,
                    )
                )
            else:
                existing.value = metric_result.value
                existing.payload_json = metric_result.payload
        return metric_result

    def list_metric_results(self, run_id: str | None = None) -> list[MetricResult]:
        with self._session_factory() as db:
            stmt = select(MetricResultModel).order_by(MetricResultModel.created_at.asc())
            if run_id is not None:
                stmt = stmt.where(MetricResultModel.run_id == run_id)
            return [
                MetricResult(
                    metric_result_id=model.metric_result_id,
                    run_id=model.run_id,
                    metric_definition_id=model.metric_definition_id,
                    name=model.name,
                    version=model.version,
                    value=model.value,
                    payload=model.payload_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    def create_formula_definition(self, formula_definition: FormulaDefinitionRecord) -> FormulaDefinitionRecord:
        with self._session_factory.begin() as db:
            db.add(
                FormulaDefinitionModel(
                    formula_definition_id=formula_definition.formula_definition_id,
                    name=formula_definition.name,
                    version=formula_definition.version,
                    status=formula_definition.status.value,
                    description=formula_definition.description,
                    input_requirements_json=formula_definition.input_requirements,
                    execution_spec_json=formula_definition.execution_spec,
                    provenance_json=formula_definition.provenance,
                    created_at=formula_definition.created_at,
                )
            )
        return formula_definition

    def get_formula_definition(self, formula_definition_id: str) -> FormulaDefinitionRecord | None:
        with self._session_factory() as db:
            model = db.get(FormulaDefinitionModel, formula_definition_id)
            if model is None:
                return None
            return FormulaDefinitionRecord(
                formula_definition_id=model.formula_definition_id,
                name=model.name,
                version=model.version,
                status=FormulaStatus(model.status),
                description=model.description,
                input_requirements=model.input_requirements_json,
                execution_spec=model.execution_spec_json,
                provenance=model.provenance_json,
                created_at=model.created_at,
            )

    def list_formula_definitions(self) -> list[FormulaDefinitionRecord]:
        with self._session_factory() as db:
            stmt = select(FormulaDefinitionModel).order_by(FormulaDefinitionModel.created_at.desc())
            return [
                FormulaDefinitionRecord(
                    formula_definition_id=model.formula_definition_id,
                    name=model.name,
                    version=model.version,
                    status=FormulaStatus(model.status),
                    description=model.description,
                    input_requirements=model.input_requirements_json,
                    execution_spec=model.execution_spec_json,
                    provenance=model.provenance_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    def create_formula_proposal(self, proposal: FormulaProposalRecord) -> FormulaProposalRecord:
        with self._session_factory.begin() as db:
            db.add(
                FormulaProposalModel(
                    formula_proposal_id=proposal.formula_proposal_id,
                    formula_definition_id=proposal.formula_definition_id,
                    source_run_id=proposal.source_run_id,
                    research_question=proposal.research_question,
                    proposal_payload_json=proposal.proposal_payload,
                    provenance_json=proposal.provenance,
                    created_at=proposal.created_at,
                )
            )
        return proposal

    def get_formula_proposal(self, formula_proposal_id: str) -> FormulaProposalRecord | None:
        with self._session_factory() as db:
            model = db.get(FormulaProposalModel, formula_proposal_id)
            if model is None:
                return None
            return FormulaProposalRecord(
                formula_proposal_id=model.formula_proposal_id,
                formula_definition_id=model.formula_definition_id,
                source_run_id=model.source_run_id,
                research_question=model.research_question,
                proposal_payload=model.proposal_payload_json,
                provenance=model.provenance_json,
                created_at=model.created_at,
            )

    def list_formula_proposals(self, formula_definition_id: str | None = None) -> list[FormulaProposalRecord]:
        with self._session_factory() as db:
            stmt = select(FormulaProposalModel).order_by(FormulaProposalModel.created_at.desc())
            if formula_definition_id is not None:
                stmt = stmt.where(FormulaProposalModel.formula_definition_id == formula_definition_id)
            return [
                FormulaProposalRecord(
                    formula_proposal_id=model.formula_proposal_id,
                    formula_definition_id=model.formula_definition_id,
                    source_run_id=model.source_run_id,
                    research_question=model.research_question,
                    proposal_payload=model.proposal_payload_json,
                    provenance=model.provenance_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    def create_formula_evaluation(self, evaluation: FormulaEvaluationRecord) -> FormulaEvaluationRecord:
        with self._session_factory.begin() as db:
            db.add(
                FormulaEvaluationModel(
                    formula_evaluation_id=evaluation.formula_evaluation_id,
                    formula_definition_id=evaluation.formula_definition_id,
                    run_id=evaluation.run_id,
                    dataset_ref=evaluation.dataset_ref,
                    summary_json=evaluation.summary,
                    provenance_json=evaluation.provenance,
                    created_at=evaluation.created_at,
                )
            )
        return evaluation

    def get_formula_evaluation(self, formula_evaluation_id: str) -> FormulaEvaluationRecord | None:
        with self._session_factory() as db:
            model = db.get(FormulaEvaluationModel, formula_evaluation_id)
            if model is None:
                return None
            return FormulaEvaluationRecord(
                formula_evaluation_id=model.formula_evaluation_id,
                formula_definition_id=model.formula_definition_id,
                run_id=model.run_id,
                dataset_ref=model.dataset_ref,
                summary=model.summary_json,
                provenance=model.provenance_json,
                created_at=model.created_at,
            )

    def list_formula_evaluations(self, formula_definition_id: str | None = None) -> list[FormulaEvaluationRecord]:
        with self._session_factory() as db:
            stmt = select(FormulaEvaluationModel).order_by(FormulaEvaluationModel.created_at.desc())
            if formula_definition_id is not None:
                stmt = stmt.where(FormulaEvaluationModel.formula_definition_id == formula_definition_id)
            return [
                FormulaEvaluationRecord(
                    formula_evaluation_id=model.formula_evaluation_id,
                    formula_definition_id=model.formula_definition_id,
                    run_id=model.run_id,
                    dataset_ref=model.dataset_ref,
                    summary=model.summary_json,
                    provenance=model.provenance_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    def create_formula_review(self, review: FormulaReviewRecord) -> FormulaReviewRecord:
        with self._session_factory.begin() as db:
            db.add(
                FormulaReviewModel(
                    formula_review_id=review.formula_review_id,
                    formula_definition_id=review.formula_definition_id,
                    formula_evaluation_id=review.formula_evaluation_id,
                    reviewer_id=review.reviewer_id,
                    verdict=review.verdict.value,
                    notes=review.notes,
                    evidence_bundle_json=review.evidence_bundle.model_dump(mode="json"),
                    provenance_json=review.provenance,
                    created_at=review.created_at,
                )
            )
        return review

    def list_formula_reviews(self, formula_definition_id: str | None = None) -> list[FormulaReviewRecord]:
        with self._session_factory() as db:
            stmt = select(FormulaReviewModel).order_by(FormulaReviewModel.created_at.desc())
            if formula_definition_id is not None:
                stmt = stmt.where(FormulaReviewModel.formula_definition_id == formula_definition_id)
            return [
                FormulaReviewRecord(
                    formula_review_id=model.formula_review_id,
                    formula_definition_id=model.formula_definition_id,
                    formula_evaluation_id=model.formula_evaluation_id,
                    reviewer_id=model.reviewer_id,
                    verdict=ReviewVerdict(model.verdict),
                    notes=model.notes,
                    evidence_bundle=ReviewEvidenceBundle(**model.evidence_bundle_json),
                    provenance=model.provenance_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    @staticmethod
    def _ensure_sqlite_parent_dir(database_url: str) -> None:
        if database_url.endswith(":memory:"):
            return
        normalized = database_url.split("///", 1)[-1]
        Path(normalized).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    def _ensure_local_runtime_validation_columns(self) -> None:
        with self.engine.begin() as connection:
            inspector = inspect(connection)
            if "assets" in inspector.get_table_names():
                columns = {column["name"] for column in inspector.get_columns("assets")}
                if "session_id" not in columns:
                    connection.execute(text("ALTER TABLE assets ADD COLUMN session_id VARCHAR"))
                if "mime_type" not in columns:
                    connection.execute(text("ALTER TABLE assets ADD COLUMN mime_type VARCHAR DEFAULT 'application/octet-stream'"))
            if "jobs" in inspector.get_table_names():
                job_columns = {column["name"] for column in inspector.get_columns("jobs")}
                if "session_id" not in job_columns:
                    connection.execute(text("ALTER TABLE jobs ADD COLUMN session_id VARCHAR"))

    @staticmethod
    def _run_model(run: RunRecord) -> RunModel:
        return RunModel(
            run_id=run.run_id,
            session_id=run.session_id,
            run_kind=run.run_kind.value,
            status=run.status.value,
            manifest_json=run.manifest.model_dump(mode="json"),
            input_asset_ids_json=list(run.input_asset_ids),
            execution_plan_json=run.execution_plan.model_dump(mode="json") if run.execution_plan else None,
            stage_results_json=[item.model_dump(mode="json") for item in run.stage_results],
            summary_json=run.summary,
            error_json=run.error,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def _write_run_model(model: RunModel, run: RunRecord) -> None:
        model.session_id = run.session_id
        model.run_kind = run.run_kind.value
        model.status = run.status.value
        model.manifest_json = run.manifest.model_dump(mode="json")
        model.input_asset_ids_json = list(run.input_asset_ids)
        model.execution_plan_json = run.execution_plan.model_dump(mode="json") if run.execution_plan else None
        model.stage_results_json = [item.model_dump(mode="json") for item in run.stage_results]
        model.summary_json = run.summary
        model.error_json = run.error
        model.created_at = run.created_at
        model.updated_at = run.updated_at

    @staticmethod
    def _read_run_model(model: RunModel) -> RunRecord:
        return RunRecord(
            run_id=model.run_id,
            session_id=model.session_id,
            run_kind=RunKind(model.run_kind),
            status=RunStatus(model.status),
            manifest=ExperimentManifest(**model.manifest_json),
            input_asset_ids=list(model.input_asset_ids_json or []),
            execution_plan=ExecutionPlan(**model.execution_plan_json) if model.execution_plan_json else None,
            stage_results=[StageResult(**item) for item in (model.stage_results_json or [])],
            summary=model.summary_json or {},
            error=model.error_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _job_model(job: JobRecord) -> JobModel:
        return JobModel(
            job_id=job.job_id,
            job_type=job.job_type.value,
            status=job.status.value,
            session_id=job.session_id,
            run_id=job.run_id,
            payload_json=job.payload,
            metadata_json=job.metadata,
            result_json=job.result,
            error_json=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    @staticmethod
    def _write_job_model(model: JobModel, job: JobRecord) -> None:
        model.job_type = job.job_type.value
        model.status = job.status.value
        model.session_id = job.session_id
        model.run_id = job.run_id
        model.payload_json = job.payload
        model.metadata_json = job.metadata
        model.result_json = job.result
        model.error_json = job.error
        model.created_at = job.created_at
        model.updated_at = job.updated_at

    @staticmethod
    def _read_job_model(model: JobModel) -> JobRecord:
        return JobRecord(
            job_id=model.job_id,
            job_type=JobType(model.job_type),
            status=JobStatus(model.status),
            session_id=model.session_id,
            run_id=model.run_id,
            payload=model.payload_json or {},
            metadata=model.metadata_json or {},
            result=model.result_json,
            error=model.error_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _asset_model(asset: AssetRecord) -> AssetModel:
        return AssetModel(
            asset_id=asset.asset_id,
            run_id=asset.run_id,
            session_id=asset.session_id,
            kind=asset.kind.value,
            blob_path=asset.blob_path,
            checksum=asset.checksum,
            mime_type=asset.mime_type,
            metadata_json=asset.metadata,
            created_at=asset.created_at,
        )

    @staticmethod
    def _write_asset_model(model: AssetModel, asset: AssetRecord) -> None:
        model.run_id = asset.run_id
        model.session_id = asset.session_id
        model.kind = asset.kind.value
        model.blob_path = asset.blob_path
        model.checksum = asset.checksum
        model.mime_type = asset.mime_type
        model.metadata_json = asset.metadata
        model.created_at = asset.created_at

    @staticmethod
    def _read_asset_model(model: AssetModel) -> AssetRecord:
        return AssetRecord(
            asset_id=model.asset_id,
            run_id=model.run_id,
            session_id=model.session_id,
            kind=AssetKind(model.kind),
            blob_path=model.blob_path,
            checksum=model.checksum,
            mime_type=model.mime_type,
            metadata=model.metadata_json or {},
            created_at=model.created_at,
        )
