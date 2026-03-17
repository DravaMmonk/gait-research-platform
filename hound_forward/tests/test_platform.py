from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from hound_forward.adapters.metadata.azure_postgres import AzurePostgresMetadataRepository
from hound_forward.adapters.queue.in_memory import InMemoryJobQueue
from hound_forward.adapters.storage.local import LocalArtifactStore
from hound_forward.agent_tools import AgentToolExecutor
from hound_forward.agent_system.graphs.research_graph import ResearchGraph
from hound_forward.agent_system.planners.experiment_planner import ExperimentManifestPlanner
from hound_forward.agent_system.tools.registry import ToolRegistry
from hound_forward.api.app import create_app
from hound_forward.application import ResearchPlatformService, ServiceContainer
from hound_forward.domain import FormulaStatus, ReviewVerdict, RunKind, RunStatus
from hound_forward.pipeline import PlatformRunExecutor
from hound_forward.worker.runtime import PlaceholderLocalWorkerBridge


def fake_openai_json_response(self, *, system_prompt, user_prompt, schema_name, schema):
    if schema_name == "intent_classification":
        if "what does this result mean" in user_prompt.lower():
            return {"intent": "explain_result"}
        if "stride length" in user_prompt.lower():
            return {"intent": "ask_question"}
        return {"intent": "run_analysis"}
    if schema_name == "general_question_response":
        return {"message": "Stride length is the distance covered in one stride cycle."}
    if schema_name == "result_explanation_response":
        return {"message": "The run completed successfully and the metrics suggest the gait pattern is interpretable."}
    raise RuntimeError(f"Unexpected schema_name: {schema_name}")


def build_service(tmp_path: Path) -> ResearchPlatformService:
    metadata = AzurePostgresMetadataRepository(f"sqlite+pysqlite:///{tmp_path / 'platform.db'}")
    metadata.create_all()
    artifact_store = LocalArtifactStore(tmp_path / "artifacts")
    queue = InMemoryJobQueue()
    tool_runner = AgentToolExecutor(artifact_store=artifact_store, work_root=tmp_path / "tool_runs")
    executor = PlatformRunExecutor(metadata=metadata, tool_runner=tool_runner)
    return ResearchPlatformService(
        ServiceContainer(metadata=metadata, artifact_store=artifact_store, queue=queue, executor=executor, tool_runner=tool_runner)
    )


def upload_video(service: ResearchPlatformService, session_id: str, name: str = "sample.mp4", content: bytes | None = None):
    return service.upload_session_video(
        session_id=session_id,
        file_name=name,
        content=content or b"fake-video-binary",
        mime_type="video/mp4",
    )


def test_upload_to_run_flow_registers_agent_tool_outputs(tmp_path: Path) -> None:
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
    assert {result.name for result in detail.metrics} == {"stride_length", "asymmetry_index", "gait_stability"}


def test_agent_metrics_are_deterministic_for_same_input_asset_and_manifest(tmp_path: Path) -> None:
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


def test_agent_vertical_slice_designs_and_executes_tool_chain(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Agent session")
    upload_video(service, session.session_id)
    graph = ResearchGraph(
        planner=ExperimentManifestPlanner(available_tools=service.container.tool_runner.describe_tools()),
        tools=ToolRegistry(service),
        worker_bridge=PlaceholderLocalWorkerBridge(service=service),
    )

    result = graph.invoke(goal="Test a new movement metric", session_id=session.session_id)
    assert result["run_status"] == "completed"
    assert "Agent tool-chain result" in result["recommendation"]
    detail = service.get_run_detail(result["run_id"])
    assert detail.run.run_kind == RunKind.AGENT_ANALYSIS
    assert any(event.status == RunStatus.COMPLETED for event in detail.events)


def test_formula_infrastructure_round_trips_records(tmp_path: Path, monkeypatch) -> None:
    service = build_service(tmp_path)
    monkeypatch.setattr(
        "hound_forward.agent_tools.video._probe_video",
        lambda path: {
            "fps": 24.0,
            "frame_count": 12,
            "duration_seconds": 0.5,
            "width": 320,
            "height": 240,
            "codec": "h264",
        },
    )
    formula = service.create_formula_definition(
        name="stride_symmetry_formula",
        version="v1",
        description="Scaffold formula definition for infrastructure validation.",
        input_requirements={"signals": ["stride_length"]},
        execution_spec={"mode": "dsl_scaffold"},
        status=FormulaStatus.PROPOSED,
    )
    proposal = service.create_formula_proposal(
        research_question="Can we normalize stride asymmetry?",
        proposal_payload={"expression": "abs(left-right)/mean(left,right)"},
        formula_definition_id=formula.formula_definition_id,
    )
    session = service.create_session(title="Formula evaluation session")
    video = upload_video(service, session.session_id)
    manifest = ExperimentManifestPlanner().plan("Formula evaluation infrastructure", dataset_video_ids=["video-001"])
    manifest.input_asset_ids = [video.asset.asset_id]
    run = service.create_run(session.session_id, manifest, run_kind=RunKind.FORMULA_EVALUATION)
    service.enqueue_run(run.run_id)
    worker = PlaceholderLocalWorkerBridge(service=service)
    completed = worker.drain_once()
    assert completed is not None
    assert completed.status == RunStatus.COMPLETED

    evaluation = service.create_formula_evaluation(
        formula_definition_id=formula.formula_definition_id,
        run_id=run.run_id,
        dataset_ref="baseline-cohort",
        summary={"stage": "scaffold"},
    )
    review = service.create_formula_review(
        formula_definition_id=formula.formula_definition_id,
        formula_evaluation_id=evaluation.formula_evaluation_id,
        reviewer_id="researcher-001",
        verdict=ReviewVerdict.NEEDS_REVISION,
        notes="Execution substrate is ready; business logic remains scaffolded.",
    )

    assert service.get_formula_definition(formula.formula_definition_id).status == FormulaStatus.PROPOSED
    assert service.list_formula_proposals(formula.formula_definition_id)[0].formula_proposal_id == proposal.formula_proposal_id
    assert service.list_formula_evaluations(formula.formula_definition_id)[0].run_id == run.run_id
    assert service.list_formula_reviews(formula.formula_definition_id)[0].reviewer_id == review.reviewer_id
    detail = service.get_run_detail(run.run_id)
    assert detail.run.run_kind == RunKind.FORMULA_EVALUATION
    assert detail.run.execution_plan is not None
    assert any(asset.metadata.get("tool_name") == "decode_video" for asset in detail.assets)


def test_tool_executor_invokes_agent_tool_and_registers_artifact(tmp_path: Path, monkeypatch) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Tool runner session")
    uploaded = upload_video(service, session.session_id, content=b"video-binary")
    monkeypatch.setattr(
        "hound_forward.agent_tools.video._probe_video",
        lambda path: {
            "fps": 24.0,
            "frame_count": 12,
            "duration_seconds": 0.5,
            "width": 320,
            "height": 240,
            "codec": "h264",
        },
    )

    result, asset = service.container.tool_runner.invoke(
        tool_name="decode_video",
        input_asset=uploaded.asset,
        run_id="tool-runner-run",
        config=None,
    )
    assert result["summary"]["tool"] == "decode_video"
    assert asset.kind.value == "report"
    assert asset.metadata["tool_name"] == "decode_video"


def test_api_surface_supports_video_upload_run_detail_and_agent_execution(tmp_path: Path) -> None:
    monkeypatch_env = {
        "HF_METADATA_DATABASE_URL": f"sqlite+pysqlite:///{tmp_path / 'api.db'}",
        "HF_ARTIFACT_ROOT": str(tmp_path / "api-artifacts"),
    }
    for key, value in monkeypatch_env.items():
        import os

        os.environ[key] = value
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

    plan_response = client.post("/agent/plan", json={"session_id": session["session_id"], "goal": "API planner flow"})
    assert plan_response.status_code == 200
    planned = plan_response.json()
    manifest = planned["manifest"]
    manifest["input_asset_ids"] = [video_asset_id]
    execution_plan = planned["execution_plan"]
    execution_plan["stages"][0]["tool_invocation"]["input_asset_id"] = video_asset_id

    run_response = client.post(
        "/runs",
        json={
            "session_id": session["session_id"],
            "manifest": manifest,
            "execution_plan": execution_plan,
        },
    )
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
    assert {item["name"] for item in metrics["metric_results"]} == {"stride_length", "asymmetry_index", "gait_stability"}

    agent_response = client.post("/agent/execute-plan", json={"session_id": session["session_id"], "goal": "Evaluate clinician cohort"})
    assert agent_response.status_code == 200
    assert agent_response.json()["run_status"] == "completed"
    assert "Agent tool-chain result" in agent_response.json()["recommendation"]


def test_api_surface_supports_formula_scaffold_endpoints(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'formula-api.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "formula-api-artifacts"))
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_graph.cache_clear()
    client = TestClient(create_app())

    formula_response = client.post(
        "/formulas/definitions",
        json={
            "name": "asymmetry_formula",
            "version": "v1",
            "description": "Infrastructure scaffold formula.",
            "input_requirements": {"signals": ["asymmetry_index"]},
            "execution_spec": {"mode": "dsl_scaffold"},
            "status": "proposed",
        },
    )
    assert formula_response.status_code == 200
    formula = formula_response.json()

    proposal_response = client.post(
        "/formulas/proposals",
        json={
            "research_question": "Can AI propose a symmetry formula?",
            "proposal_payload": {"expression": "abs(left-right)/mean(left,right)"},
            "formula_definition_id": formula["formula_definition_id"],
        },
    )
    assert proposal_response.status_code == 200

    review_response = client.post(
        "/formulas/reviews",
        json={
            "formula_definition_id": formula["formula_definition_id"],
            "reviewer_id": "researcher-001",
            "verdict": "needs_revision",
            "notes": "Scaffold review.",
            "evidence_bundle": {"asset_ids": [], "metric_result_ids": []},
        },
    )
    assert review_response.status_code == 200

    assert client.get("/formulas/definitions").status_code == 200
    assert client.get("/formulas/proposals").status_code == 200
    assert client.get("/formulas/reviews").status_code == 200


def test_api_surface_supports_console_agent_response(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'console-api.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "console-api-artifacts"))
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_graph.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Console session", "metadata": {"source": "test"}})
    assert session_response.status_code == 200
    session = session_response.json()

    response = client.post(
        "/agent/console/respond",
        json={
            "session_id": session["session_id"],
            "message": "Compare this dog's mobility over the last 6 months and show as table only.",
            "display_preferences": ["table_only"],
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["message"]
    assert payload["view_modes"][0] == "table"
    assert payload["modules"]
    assert {item["type"] for item in payload["modules"]} == {"metric_table", "evidence_panel"}
    assert payload["evidence_context"]["derived_metric"] is False
    assert payload["tool_trace"]
    assert "controlled visual modules" not in payload["message"]


def test_console_agent_response_executes_langgraph_when_video_is_available(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'console-run-api.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "console-run-api-artifacts"))
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_graph.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Console run session", "metadata": {"source": "test"}})
    assert session_response.status_code == 200
    session = session_response.json()

    upload_response = client.post(
        f"/sessions/{session['session_id']}/videos",
        files={"file": ("sample.mp4", b"fake-video-binary", "video/mp4")},
    )
    assert upload_response.status_code == 200

    response = client.post(
        "/agent/console/respond",
        json={
            "session_id": session["session_id"],
            "message": "Evaluate clinician cohort",
            "display_preferences": [],
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert "I ran" in payload["message"]
    assert "Agent tool-chain result" in payload["message"]
    assert payload["evidence_context"]["derived_metric"] is True
    assert {item["tool_name"] for item in payload["tool_trace"]} >= {"planner", "langgraph_execute", "read_metrics"}


def test_api_chat_runs_analysis_and_returns_progress_messages(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'chat-api.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "chat-api-artifacts"))
    monkeypatch.setattr(
        "hound_forward.agent_system.chat.intent_router.OpenAIResponsesJSONClient.create_json",
        fake_openai_json_response,
    )
    monkeypatch.setattr(
        "hound_forward.agent_system.chat.reasoner.OpenAIResponsesJSONClient.create_json",
        fake_openai_json_response,
    )
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_graph.cache_clear()
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Chat session"})
    session = session_response.json()
    client.post(
        f"/sessions/{session['session_id']}/videos",
        files={"file": ("sample.mp4", b"fake-video-binary", "video/mp4")},
    )

    response = client.post(
        "/api/chat",
        json={"session_id": session["session_id"], "message": "Analyze my dog's gait"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["type"] == "run"
    assert payload["run_id"]
    assert payload["progress_messages"]
    assert payload["structured_data"]["execution_plan"]["stages"]
    assert payload["structured_data"]["metrics"]


def test_api_chat_answers_question_without_run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'chat-question.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "chat-question-artifacts"))
    monkeypatch.setattr(
        "hound_forward.agent_system.chat.intent_router.OpenAIResponsesJSONClient.create_json",
        fake_openai_json_response,
    )
    monkeypatch.setattr(
        "hound_forward.agent_system.chat.reasoner.OpenAIResponsesJSONClient.create_json",
        fake_openai_json_response,
    )
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_graph.cache_clear()
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Question session"})
    session = session_response.json()

    response = client.post(
        "/api/chat",
        json={"session_id": session["session_id"], "message": "What is stride length?"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["type"] == "text"
    assert payload["run_id"] is None
    assert payload["message"] == "Stride length is the distance covered in one stride cycle."


def test_api_chat_explains_existing_run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'chat-explain.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "chat-explain-artifacts"))
    monkeypatch.setattr(
        "hound_forward.agent_system.chat.intent_router.OpenAIResponsesJSONClient.create_json",
        fake_openai_json_response,
    )
    monkeypatch.setattr(
        "hound_forward.agent_system.chat.reasoner.OpenAIResponsesJSONClient.create_json",
        fake_openai_json_response,
    )
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_graph.cache_clear()
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Explain session"})
    session = session_response.json()
    client.post(
        f"/sessions/{session['session_id']}/videos",
        files={"file": ("sample.mp4", b"fake-video-binary", "video/mp4")},
    )
    run_response = client.post(
        "/api/chat",
        json={"session_id": session["session_id"], "message": "Analyze my dog's gait"},
    )
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/api/chat",
        json={
            "session_id": session["session_id"],
            "message": "What does this result mean?",
            "context": {"run_id": run_id},
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["type"] == "text"
    assert payload["run_id"] == run_id
    assert payload["structured_data"]["source_run_id"] == run_id
