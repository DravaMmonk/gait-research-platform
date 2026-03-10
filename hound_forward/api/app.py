from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from hound_forward.adapters.metadata.azure_postgres import AzurePostgresMetadataRepository
from hound_forward.adapters.queue.in_memory import InMemoryJobQueue
from hound_forward.adapters.storage.local import LocalArtifactStore
from hound_forward.agent_system.graphs.research_graph import ResearchGraph
from hound_forward.agent_system.planners.experiment_planner import ExperimentManifestPlanner
from hound_forward.agent_system.tools.registry import ToolRegistry
from hound_forward.application import ResearchPlatformService, ServiceContainer
from hound_forward.domain import ExperimentManifest, RunKind
from hound_forward.pipeline import DummyRuntimeValidationPipeline
from hound_forward.settings import PlatformSettings


class SessionCreateRequest(BaseModel):
    title: str
    dog_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class RunCreateRequest(BaseModel):
    session_id: str
    manifest: ExperimentManifest
    run_kind: RunKind = RunKind.PIPELINE


class AgentPlanRequest(BaseModel):
    session_id: str
    goal: str


@lru_cache(maxsize=1)
def build_service() -> ResearchPlatformService:
    settings = PlatformSettings()
    metadata = AzurePostgresMetadataRepository(settings.metadata_database_url)
    metadata.create_all()
    artifact_store = LocalArtifactStore(settings.artifact_root_path())
    queue = InMemoryJobQueue()
    executor = DummyRuntimeValidationPipeline(artifact_store=artifact_store, metadata=metadata)
    return ResearchPlatformService(ServiceContainer(metadata=metadata, artifact_store=artifact_store, queue=queue, executor=executor))


@lru_cache(maxsize=1)
def build_graph() -> ResearchGraph:
    service = build_service()
    planner = ExperimentManifestPlanner(default_runner=PlatformSettings().default_runner)
    tools = ToolRegistry(service)
    return ResearchGraph(planner=planner, tools=tools)


def create_app() -> FastAPI:
    app = FastAPI(title=PlatformSettings().api_title)
    service = build_service()
    graph = build_graph()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "hound-forward-api"}

    @app.post("/sessions")
    def create_session(request: SessionCreateRequest) -> dict:
        session = service.create_session(title=request.title, dog_id=request.dog_id, metadata=request.metadata)
        return session.model_dump(mode="json")

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict:
        session = service.container.metadata.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.model_dump(mode="json")

    @app.post("/sessions/{session_id}/videos")
    async def upload_video(session_id: str, file: UploadFile = File(...)) -> dict:
        try:
            uploaded = service.upload_session_video(
                session_id=session_id,
                file_name=file.filename or "uploaded-video.mp4",
                content=await file.read(),
                mime_type=file.content_type or "video/mp4",
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return uploaded.model_dump(mode="json")

    @app.get("/sessions/{session_id}/videos")
    def list_session_videos(session_id: str) -> dict:
        return {
            "session_id": session_id,
            "videos": [item.model_dump(mode="json") for item in service.list_session_videos(session_id)],
            "placeholder_flags": {"dummy": True, "fake": False, "placeholder": True},
        }

    @app.post("/runs")
    def create_run(request: RunCreateRequest) -> dict:
        try:
            run = service.create_run(session_id=request.session_id, manifest=request.manifest, run_kind=request.run_kind)
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return run.model_dump(mode="json")

    @app.post("/runs/{run_id}:enqueue")
    def enqueue_run(run_id: str) -> dict:
        run = service.enqueue_run(run_id)
        return run.model_dump(mode="json")

    @app.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict:
        try:
            run = service.get_run(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return run.model_dump(mode="json")

    @app.get("/runs")
    def list_runs(session_id: str | None = None) -> dict:
        return {"runs": [item.model_dump(mode="json") for item in service.list_runs(session_id=session_id)]}

    @app.get("/runs/{run_id}/assets")
    def list_assets(run_id: str) -> dict:
        return {"assets": [item.model_dump(mode="json") for item in service.list_assets(run_id)]}

    @app.get("/runs/{run_id}/detail")
    def get_run_detail(run_id: str) -> dict:
        try:
            detail = service.get_run_detail(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return detail.model_dump(mode="json")

    @app.get("/runs/{run_id}/metrics")
    def read_run_metrics(run_id: str) -> dict:
        try:
            metrics = service.read_metrics(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return metrics.model_dump(mode="json")

    @app.get("/metrics")
    def list_metrics(run_id: str | None = None) -> dict:
        return {
            "definitions": [item.model_dump(mode="json") for item in service.list_metric_definitions()],
            "results": [item.model_dump(mode="json") for item in service.list_metric_results(run_id=run_id)],
        }

    @app.post("/agent/plan")
    def agent_plan(request: AgentPlanRequest) -> dict:
        manifest = ExperimentManifestPlanner(default_runner=PlatformSettings().default_runner).plan(goal=request.goal)
        return manifest.model_dump(mode="json")

    @app.post("/agent/execute-plan")
    def agent_execute_plan(request: AgentPlanRequest) -> dict:
        return graph.invoke(goal=request.goal, session_id=request.session_id)

    return app


app = create_app()
