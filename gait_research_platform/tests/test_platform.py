from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from hound_forward.adapters.metadata.azure_postgres import AzurePostgresMetadataRepository
from hound_forward.adapters.queue.in_memory import InMemoryJobQueue
from hound_forward.adapters.storage.local import LocalArtifactStore
from hound_forward.agent_system.graphs.research_graph import ResearchGraph
from hound_forward.agent_system.planners.experiment_planner import ExperimentManifestPlanner
from hound_forward.agent_system.tools.registry import ToolRegistry
from hound_forward.api.app import create_app
from hound_forward.application import ResearchPlatformService, ServiceContainer
from hound_forward.domain import ExperimentManifest, RunStatus
from hound_forward.pipeline import DeterministicLocalRunExecutor


def build_service(tmp_path: Path) -> ResearchPlatformService:
    metadata = AzurePostgresMetadataRepository(f"sqlite+pysqlite:///{tmp_path / 'platform.db'}")
    metadata.create_all()
    artifact_store = LocalArtifactStore(tmp_path / "artifacts")
    queue = InMemoryJobQueue()
    executor = DeterministicLocalRunExecutor(artifact_store=artifact_store, metadata=metadata)
    return ResearchPlatformService(ServiceContainer(metadata=metadata, artifact_store=artifact_store, queue=queue, executor=executor))


def test_run_lifecycle_persists_metadata_and_assets(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Clinical gait review", dog_id="dog-001")
    manifest = ExperimentManifestPlanner().plan("Evaluate stride asymmetry", dataset_video_ids=["video-001", "video-002"])

    run = service.create_run(session_id=session.session_id, manifest=manifest)
    assert run.status == RunStatus.PENDING
    assert len(service.list_assets(run.run_id)) == 1

    queued = service.enqueue_run(run.run_id)
    assert queued.status == RunStatus.QUEUED

    completed = service.process_next_job()
    assert completed is not None
    assert completed.status == RunStatus.SUCCEEDED
    assert completed.summary["dataset_size"] == 2
    assert len(service.list_assets(run.run_id)) == 3
    assert len(service.list_metric_results(run.run_id)) == 2


def test_compare_runs_returns_metric_delta(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Comparison session")
    planner = ExperimentManifestPlanner()

    first = service.create_run(session.session_id, planner.plan("Baseline", dataset_video_ids=["video-001"]))
    second = service.create_run(session.session_id, planner.plan("Expanded cohort", dataset_video_ids=["video-001", "video-002", "video-003"]))

    service.enqueue_run(first.run_id)
    service.process_next_job()
    service.enqueue_run(second.run_id)
    service.process_next_job()

    comparison = service.compare_runs(first.run_id, second.run_id)
    assert comparison["left_run_id"] == first.run_id
    assert comparison["right_run_id"] == second.run_id
    assert any(metric["name"] == "gait_stability" for metric in comparison["metrics"])


def test_langgraph_research_loop_executes_via_tools(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Agent session")
    graph = ResearchGraph(planner=ExperimentManifestPlanner(), tools=ToolRegistry(service))

    result = graph.invoke(goal="Test a new movement metric", session_id=session.session_id)
    assert result["run_status"] == "succeeded"
    assert "recommendation" in result
    assert len(service.list_metric_results(result["run_id"])) == 2


def test_api_surface_supports_sessions_runs_and_agent_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "api-artifacts"))
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_graph.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "API session", "dog_id": "dog-123"})
    assert session_response.status_code == 200
    session = session_response.json()

    manifest = ExperimentManifestPlanner().plan("API planner flow").model_dump(mode="json")
    run_response = client.post("/runs", json={"session_id": session["session_id"], "manifest": manifest})
    assert run_response.status_code == 200
    run = run_response.json()

    enqueue_response = client.post(f"/runs/{run['run_id']}:enqueue")
    assert enqueue_response.status_code == 200
    assert enqueue_response.json()["status"] == "queued"

    agent_response = client.post("/agent/execute-plan", json={"session_id": session["session_id"], "goal": "Evaluate clinician cohort"})
    assert agent_response.status_code == 200
    assert agent_response.json()["run_status"] == "succeeded"
