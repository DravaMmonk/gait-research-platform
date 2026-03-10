from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from hound_forward.domain import (
    AssetKind,
    AssetRecord,
    ExperimentManifest,
    MetricDefinition,
    MetricResult,
    RunEvent,
    RunKind,
    RunRecord,
    RunStatus,
    SessionRecord,
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


class AssetModel(Base):
    __tablename__ = "assets"

    asset_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
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


class AzurePostgresMetadataRepository:
    """Metadata repository aligned to Azure PostgreSQL schema semantics."""

    def __init__(self, database_url: str) -> None:
        engine_kwargs: dict[str, Any] = {"future": True}
        if database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            if database_url.endswith(":memory:"):
                engine_kwargs["poolclass"] = StaticPool
        self.engine = create_engine(database_url, **engine_kwargs)
        self._session_factory = sessionmaker(self.engine, expire_on_commit=False, class_=Session)

    def create_all(self) -> None:
        Base.metadata.create_all(self.engine)

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

    def create_run(self, run: RunRecord) -> RunRecord:
        with self._session_factory.begin() as db:
            db.add(
                RunModel(
                    run_id=run.run_id,
                    session_id=run.session_id,
                    run_kind=run.run_kind.value,
                    status=run.status.value,
                    manifest_json=run.manifest.model_dump(mode="json"),
                    summary_json=run.summary,
                    error_json=run.error,
                    created_at=run.created_at,
                    updated_at=run.updated_at,
                )
            )
        return run

    def update_run(self, run: RunRecord) -> RunRecord:
        with self._session_factory.begin() as db:
            model = db.get(RunModel, run.run_id)
            if model is None:
                raise KeyError(f"Unknown run_id: {run.run_id}")
            model.status = run.status.value
            model.summary_json = run.summary
            model.error_json = run.error
            model.updated_at = run.updated_at
            model.manifest_json = run.manifest.model_dump(mode="json")
        return run

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._session_factory() as db:
            model = db.get(RunModel, run_id)
            if model is None:
                return None
            return self._to_run_record(model)

    def list_runs(self, session_id: str | None = None) -> list[RunRecord]:
        with self._session_factory() as db:
            stmt = select(RunModel).order_by(RunModel.created_at.desc())
            if session_id is not None:
                stmt = stmt.where(RunModel.session_id == session_id)
            return [self._to_run_record(model) for model in db.scalars(stmt)]

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
            db.add(
                AssetModel(
                    asset_id=asset.asset_id,
                    run_id=asset.run_id,
                    kind=asset.kind.value,
                    blob_path=asset.blob_path,
                    checksum=asset.checksum,
                    mime_type=asset.mime_type,
                    metadata_json=asset.metadata,
                    created_at=asset.created_at,
                )
            )
        return asset

    def list_assets(self, run_id: str) -> list[AssetRecord]:
        with self._session_factory() as db:
            stmt = select(AssetModel).where(AssetModel.run_id == run_id).order_by(AssetModel.created_at.asc())
            return [
                AssetRecord(
                    asset_id=model.asset_id,
                    run_id=model.run_id,
                    kind=AssetKind(model.kind),
                    blob_path=model.blob_path,
                    checksum=model.checksum,
                    mime_type=model.mime_type,
                    metadata=model.metadata_json,
                    created_at=model.created_at,
                )
                for model in db.scalars(stmt)
            ]

    def register_metric_definition(self, metric_definition: MetricDefinition) -> MetricDefinition:
        with self._session_factory.begin() as db:
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

    def compare_runs(self, left_run_id: str, right_run_id: str) -> dict[str, Any]:
        left = {item.name: item.value for item in self.list_metric_results(run_id=left_run_id)}
        right = {item.name: item.value for item in self.list_metric_results(run_id=right_run_id)}
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

    @staticmethod
    def _to_run_record(model: RunModel) -> RunRecord:
        return RunRecord(
            run_id=model.run_id,
            session_id=model.session_id,
            run_kind=RunKind(model.run_kind),
            status=RunStatus(model.status),
            manifest=ExperimentManifest.model_validate(model.manifest_json),
            summary=model.summary_json,
            error=model.error_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
