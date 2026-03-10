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
from hound_forward.domain import RunStatus
from hound_forward.pipeline import DummyRuntimeValidationPipeline
from hound_forward.worker.runtime import PlaceholderLocalWorkerBridge


def build_service(tmp_path: Path) -> ResearchPlatformService:
    metadata = AzurePostgresMetadataRepository(f"sqlite+pysqlite:///{tmp_path / 'platform.db'}")
    metadata.create_all()
    artifact_store = LocalArtifactStore(tmp_path / "artifacts")
    queue = InMemoryJobQueue()
    executor = DummyRuntimeValidationPipeline(artifact_store=artifact_store, metadata=metadata)
    return ResearchPlatformService(ServiceContainer(metadata=metadata, artifact_store=artifact_store, queue=queue, executor=executor))


def upload_video(service: ResearchPlatformService, session_id: str, name: str = "sample.mp4", content: bytes | None = None):
    return service.upload_session_video(
        session_id=session_id,
        file_name=name,
        content=content or b"fake-video-binary",
        mime_type="video/mp4",
    )


def test_upload_to_run_flow_registers_dummy_outputs(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Clinical gait review", dog_id="dog-001")
    video = upload_video(service, session.session_id)
    manifest = ExperimentManifestPlanner().plan("Evaluate stride asymmetry", dataset_video_ids=["uploaded-video-001"])
    manifest.input_asset_ids = [video.asset.asset_id]

    run = service.create_run(session_id=session.session_id, manifest=manifest)
    assert run.status == RunStatus.CREATED
    assert run.input_asset_ids == [video.asset.asset_id]

    queued = service.enqueue_run(run.run_id)
    assert queued.status == RunStatus.QUEUED

    worker = PlaceholderLocalWorkerBridge(service=service)
    completed = worker.drain_once()
    assert completed is not None
    assert completed.status == RunStatus.COMPLETED

    detail = service.get_run_detail(run.run_id)
    assert detail.run.status == RunStatus.COMPLETED
    assert any(asset.kind.value == "video" for asset in detail.assets)
    assert any(asset.kind.value == "keypoints" for asset in detail.assets)
    assert any(asset.kind.value == "metric_result" for asset in detail.assets)
    assert any(asset.kind.value == "report" for asset in detail.assets)
    assert {result.name for result in detail.metrics} == {"stride_length", "asymmetry_index"}


def test_dummy_metrics_are_deterministic_for_same_input_asset_and_manifest(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Determinism session")
    video = upload_video(service, session.session_id, content=b"same-video-content")

    planner = ExperimentManifestPlanner()
    manifest_a = planner.plan("Baseline video validation", dataset_video_ids=["video-001"])
    manifest_a.input_asset_ids = [video.asset.asset_id]
    manifest_a.id = "fixed-manifest-id"
    manifest_b = planner.plan("Baseline video validation", dataset_video_ids=["video-001"])
    manifest_b.input_asset_ids = [video.asset.asset_id]
    manifest_b.id = "fixed-manifest-id"

    run_a = service.create_run(session.session_id, manifest_a)
    run_b = service.create_run(session.session_id, manifest_b)
    service.enqueue_run(run_a.run_id)
    service.enqueue_run(run_b.run_id)
    worker = PlaceholderLocalWorkerBridge(service=service)
    worker.drain_once()
    worker.drain_once()

    metrics_a = service.read_metrics(run_a.run_id)
    metrics_b = service.read_metrics(run_b.run_id)
    values_a = {item.name: item.value for item in metrics_a.metric_results}
    values_b = {item.name: item.value for item in metrics_b.metric_results}
    assert values_a == values_b


def test_agent_vertical_slice_requires_uploaded_video_and_mentions_dummy_pipeline(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Agent session")
    upload_video(service, session.session_id)
    graph = ResearchGraph(
        planner=ExperimentManifestPlanner(),
        tools=ToolRegistry(service),
        worker_bridge=PlaceholderLocalWorkerBridge(service=service),
    )

    result = graph.invoke(goal="Test a new movement metric", session_id=session.session_id)
    assert result["run_status"] == "completed"
    assert "Dummy runtime validation result" in result["recommendation"]
    detail = service.get_run_detail(result["run_id"])
    assert any(event.status == RunStatus.COMPLETED for event in detail.events)


def test_api_surface_supports_video_upload_run_detail_and_agent_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'api.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "api-artifacts"))
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_graph.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "API session", "dog_id": "dog-123"})
    assert session_response.status_code == 200
    session = session_response.json()

    upload_response = client.post(
        f"/sessions/{session['session_id']}/videos",
        files={"file": ("sample.mp4", b"binary-video-content", "video/mp4")},
    )
    assert upload_response.status_code == 200
    video_asset_id = upload_response.json()["asset"]["asset_id"]

    manifest = ExperimentManifestPlanner().plan("API planner flow").model_dump(mode="json")
    manifest["input_asset_ids"] = [video_asset_id]
    run_response = client.post("/runs", json={"session_id": session["session_id"], "manifest": manifest})
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["status"] == "created"

    enqueue_response = client.post(f"/runs/{run['run_id']}:enqueue")
    assert enqueue_response.status_code == 200
    assert enqueue_response.json()["status"] == "queued"

    bridge = PlaceholderLocalWorkerBridge(service=app_module.build_service())
    bridge.drain_once()

    detail_response = client.get(f"/runs/{run['run_id']}/detail")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["run"]["status"] == "completed"
    assert any(asset["kind"] == "video" for asset in detail["assets"])

    metrics_response = client.get(f"/runs/{run['run_id']}/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["metrics_asset"]["kind"] == "metric_result"
    assert {item["name"] for item in metrics["metric_results"]} == {"stride_length", "asymmetry_index"}

    agent_response = client.post("/agent/execute-plan", json={"session_id": session["session_id"], "goal": "Evaluate clinician cohort"})
    assert agent_response.status_code == 200
    assert agent_response.json()["run_status"] == "completed"
    assert "Dummy runtime validation result" in agent_response.json()["recommendation"]
