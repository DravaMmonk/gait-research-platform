from __future__ import annotations

import base64
import importlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from hound_forward.adapters.metadata import SqlAlchemyMetadataRepository
from hound_forward.adapters.queue.gcp_pubsub import PubSubJobQueue
from hound_forward.adapters.queue.in_memory import InMemoryJobQueue
from hound_forward.adapters.storage.local import LocalArtifactStore
from hound_forward.agent_tools import AgentToolExecutor
from hound_forward.agent_system.graphs.research_graph import ResearchGraph
from hound_forward.agent_system.planners.experiment_planner import ExperimentManifestPlanner
from hound_forward.agent_system.tools.registry import ToolRegistry
from hound_forward.agent.service import create_app as create_agent_service_app
from hound_forward.api.app import create_app
from hound_forward.application import ResearchPlatformService, ServiceContainer
from hound_forward.bootstrap import build_artifact_store, build_queue
from hound_forward.domain import FormulaStatus, ReviewVerdict, RunKind, RunStatus
from hound_forward.pipeline import PlatformRunExecutor
from hound_forward.ports import Job, serialize_job
from hound_forward.settings import PlatformSettings
from hound_forward.worker.runtime import InlineRunMonitor
from hound_forward.worker.service import create_app as create_worker_service_app


def fake_openai_json_response(self, *, system_prompt, user_prompt, schema_name, schema):
    if schema_name == "intent_classification":
        if "what tools can you call" in user_prompt.lower():
            return {"intent": "ask_question"}
        if "uploaded video assets in the current session" in user_prompt.lower():
            return {"intent": "ask_question"}
        if "what does this result mean" in user_prompt.lower():
            return {"intent": "explain_result"}
        if "stride length" in user_prompt.lower():
            return {"intent": "ask_question"}
        return {"intent": "run_analysis"}
    if schema_name == "tool_inventory_response":
        return {
            "message": (
                "I can call platform registry tools such as create_run and read_metrics, "
                "and graph execution tools such as decode_video, extract_keypoints, "
                "compute_gait_metrics, and generate_report."
            )
        }
    if schema_name == "general_question_response":
        return {"message": "Stride length is the distance covered in one stride cycle."}
    if schema_name == "result_explanation_response":
        return {"message": "The run completed successfully and the metrics suggest the gait pattern is interpretable."}
    raise RuntimeError(f"Unexpected schema_name: {schema_name}")


def build_service(tmp_path: Path) -> ResearchPlatformService:
    metadata = SqlAlchemyMetadataRepository(f"sqlite+pysqlite:///{tmp_path / 'platform.db'}")
    metadata.create_all()
    artifact_store = LocalArtifactStore(tmp_path / "artifacts")
    queue = InMemoryJobQueue(queue_name="runs")
    tool_runner = AgentToolExecutor(artifact_store=artifact_store, work_root=tmp_path / "tool_runs")
    executor = PlatformRunExecutor(metadata=metadata, tool_runner=tool_runner)
    return ResearchPlatformService(
        ServiceContainer(
            metadata=metadata,
            artifact_store=artifact_store,
            run_queue=queue,
            agent_queue=InMemoryJobQueue(queue_name="agent-runs"),
            executor=executor,
            tool_runner=tool_runner,
        )
    )


def upload_video(service: ResearchPlatformService, session_id: str, name: str = "sample.mp4", content: bytes | None = None):
    return service.upload_session_video(
        session_id=session_id,
        file_name=name,
        content=content or b"fake-video-binary",
        mime_type="video/mp4",
    )


def encode_pubsub_job(job: Job) -> dict:
    encoded = base64.b64encode(json.dumps(serialize_job(job)).encode("utf-8")).decode("utf-8")
    return {"message": {"data": encoded}}


def test_session_attachment_upload_supports_image_and_text_assets(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Attachment session")

    image = service.upload_session_attachment(
        session_id=session.session_id,
        file_name="frame.png",
        content=b"fake-image-binary",
        mime_type="image/png",
    )
    text = service.upload_session_attachment(
        session_id=session.session_id,
        file_name="notes.txt",
        content=b"gait notes",
        mime_type="text/plain",
    )

    attachments = service.list_session_attachments(session.session_id)

    assert image.asset.kind.value == "image"
    assert text.asset.kind.value == "text"
    assert {item.kind.value for item in attachments} >= {"image", "text"}
    assert image.asset.metadata["original_file_name"] == "frame.png"
    assert text.asset.metadata["original_file_name"] == "notes.txt"


def test_session_attachment_upload_rejects_unsupported_types(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Unsupported attachment session")

    try:
        service.upload_session_attachment(
            session_id=session.session_id,
            file_name="archive.zip",
            content=b"not-supported",
            mime_type="application/zip",
        )
    except ValueError as exc:
        assert "Unsupported attachment type" in str(exc)
    else:
        raise AssertionError("Expected unsupported attachment upload to fail.")


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

    worker = InlineRunMonitor(service=service)
    completed = worker.wait_for_terminal_state(run.run_id)
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
    worker = InlineRunMonitor(service=service)
    worker.wait_for_terminal_state(run_a.run_id)
    worker.wait_for_terminal_state(run_b.run_id)

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
        run_monitor=InlineRunMonitor(service=service),
    )

    result = graph.invoke(goal="Test a new movement metric", session_id=session.session_id)
    assert result["run_status"] == "completed"
    assert "Agent tool-chain result" in result["recommendation"]
    detail = service.get_run_detail(result["run_id"])
    assert detail.run.run_kind == RunKind.AGENT_ANALYSIS
    assert any(event.status == RunStatus.COMPLETED for event in detail.events)


def test_get_run_logs_tool_returns_events_jobs_and_report_preview(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    session = service.create_session(title="Run log session")
    upload_video(service, session.session_id)
    graph = ResearchGraph(
        planner=ExperimentManifestPlanner(available_tools=service.container.tool_runner.describe_tools()),
        tools=ToolRegistry(service),
        run_monitor=InlineRunMonitor(service=service),
    )

    result = graph.invoke(goal="Generate a gait analysis report", session_id=session.session_id)
    payload = service.tool_get_run_logs(result["run_id"]).data

    assert payload["run"]["run_id"] == result["run_id"]
    assert any(event["status"] == "completed" for event in payload["events"])
    assert any(job["job_type"] == "run_execution" for job in payload["jobs"])
    assert payload["report_assets"]
    report_preview = payload["report_assets"][0]["preview"]
    assert report_preview["available"] is True
    assert report_preview["format"] == "json"
    assert report_preview["content"]["summary"]["tool"] == "generate_report"


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
    worker = InlineRunMonitor(service=service)
    completed = worker.wait_for_terminal_state(run.run_id)
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

    bridge = InlineRunMonitor(service=app_module.build_service())
    bridge.wait_for_terminal_state(run["run_id"])

    detail_response = client.get(f"/runs/{run['run_id']}/detail")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["run"]["status"] == "completed"


def test_api_surface_supports_session_attachment_upload_and_listing(tmp_path: Path) -> None:
    monkeypatch_env = {
        "HF_METADATA_DATABASE_URL": f"sqlite+pysqlite:///{tmp_path / 'api-attachments.db'}",
        "HF_ARTIFACT_ROOT": str(tmp_path / "api-attachments-artifacts"),
    }
    for key, value in monkeypatch_env.items():
        import os

        os.environ[key] = value
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Attachment API session"})
    session = session_response.json()

    image_response = client.post(
        f"/sessions/{session['session_id']}/attachments",
        files={"file": ("frame.png", b"fake-image-binary", "image/png")},
    )
    assert image_response.status_code == 200
    assert image_response.json()["asset"]["kind"] == "image"

    text_response = client.post(
        f"/sessions/{session['session_id']}/attachments",
        files={"file": ("notes.txt", b"clinical notes", "text/plain")},
    )
    assert text_response.status_code == 200
    assert text_response.json()["asset"]["kind"] == "text"

    list_response = client.get(f"/sessions/{session['session_id']}/attachments")
    assert list_response.status_code == 200
    attachments = list_response.json()["attachments"]
    assert {item["kind"] for item in attachments} >= {"image", "text"}
    assert {item["metadata"]["original_file_name"] for item in attachments} >= {"frame.png", "notes.txt"}


def test_api_surface_rejects_unsupported_session_attachment_type(tmp_path: Path) -> None:
    monkeypatch_env = {
        "HF_METADATA_DATABASE_URL": f"sqlite+pysqlite:///{tmp_path / 'api-attachments-invalid.db'}",
        "HF_ARTIFACT_ROOT": str(tmp_path / "api-attachments-invalid-artifacts"),
    }
    for key, value in monkeypatch_env.items():
        import os

        os.environ[key] = value
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Attachment reject session"})
    session = session_response.json()

    response = client.post(
        f"/sessions/{session['session_id']}/attachments",
        files={"file": ("archive.zip", b"zip-binary", "application/zip")},
    )
    assert response.status_code == 400
    assert "Unsupported attachment type" in response.json()["detail"]

    agent_response = client.post("/agent/execute-plan", json={"session_id": session["session_id"], "goal": "Evaluate clinician cohort"})
    assert agent_response.status_code == 200
    assert agent_response.json()["job_type"] == "agent_execution"
    assert agent_response.json()["status"] == "pending"


def test_api_surface_lists_and_deletes_sessions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'session-admin.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "session-admin-artifacts"))
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    first = client.post("/sessions", json={"title": "Session A"}).json()
    second = client.post("/sessions", json={"title": "Session B"}).json()

    list_response = client.get("/sessions")
    assert list_response.status_code == 200
    listed_ids = {item["session_id"] for item in list_response.json()["sessions"]}
    assert {first["session_id"], second["session_id"]} <= listed_ids

    delete_response = client.delete(f"/sessions/{first['session_id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    refreshed_ids = {item["session_id"] for item in client.get("/sessions").json()["sessions"]}
    assert first["session_id"] not in refreshed_ids
    assert second["session_id"] in refreshed_ids


def test_api_surface_supports_formula_scaffold_endpoints(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'formula-api.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "formula-api-artifacts"))
    app_module = importlib.import_module("hound_forward.api.app")

    app_module.build_service.cache_clear()
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


def test_api_chat_reports_registered_tools_for_tool_inventory_question(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'chat-tools.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "chat-tools-artifacts"))
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
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Tool inventory session"})
    session = session_response.json()

    response = client.post(
        "/api/chat",
        json={"session_id": session["session_id"], "message": "What tools can you call right now?"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["type"] == "text"
    assert "create_run" in payload["message"]
    assert "extract_keypoints" in payload["message"]
    tool_names = {tool["name"] for tool in payload["structured_data"]["available_tools"]}
    assert {"create_run", "read_metrics", "decode_video", "extract_keypoints", "get_run_logs"} <= tool_names


def test_api_exposes_run_logs_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'run-logs.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "run-logs-artifacts"))
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
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    session = client.post("/sessions", json={"title": "Run log API session"}).json()
    client.post(
        f"/sessions/{session['session_id']}/videos",
        files={"file": ("sample.mp4", b"fake-video-binary", "video/mp4")},
    )
    run_response = client.post(
        "/api/chat",
        json={"session_id": session["session_id"], "message": "Analyze my dog's gait"},
    )
    run_id = run_response.json()["run_id"]

    response = client.get(f"/runs/{run_id}/logs")
    assert response.status_code == 200
    payload = response.json()

    assert payload["run"]["run_id"] == run_id
    assert payload["jobs"]
    assert payload["report_assets"]


def test_api_chat_lists_current_session_videos_without_requiring_session_id_in_message(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'chat-videos.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "chat-videos-artifacts"))
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
    app_module.build_chat_orchestrator.cache_clear()
    client = TestClient(create_app())

    session_response = client.post("/sessions", json={"title": "Video session"})
    session = session_response.json()
    client.post(
        f"/sessions/{session['session_id']}/videos",
        files={"file": ("sample.mp4", b"fake-video-binary", "video/mp4")},
    )

    response = client.post(
        "/api/chat",
        json={"session_id": session["session_id"], "message": "List the uploaded video assets in the current session."},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["type"] == "text"
    assert "current session" in payload["message"].lower()
    assert "sample.mp4" in payload["message"]
    assert payload["structured_data"]["current_session_videos"]


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


def test_build_queue_supports_gcp_pubsub_settings() -> None:
    settings = PlatformSettings(
        queue_backend="gcp_pubsub",
        gcp_project_id="test-project",
        gcp_pubsub_run_topic="runs-topic",
        gcp_pubsub_run_subscription="runs-subscription",
    )

    queue = build_queue(
        settings=settings,
        queue_name=settings.queue.run.name,
        topic=settings.queue.run.topic,
        subscription=settings.queue.run.subscription,
    )

    assert isinstance(queue, PubSubJobQueue)
    assert queue.project_id == "test-project"
    assert queue.topic == "runs-topic"
    assert queue.subscription == "runs-subscription"


def test_build_artifact_store_requires_bucket_for_gcs_backend(tmp_path: Path) -> None:
    settings = PlatformSettings(
        artifact_backend="gcs",
        artifact_root=tmp_path / "artifacts",
        gcp_project_id="test-project",
    )

    try:
        build_artifact_store(settings)
    except ValueError as exc:
        assert "HF_GCP_STORAGE_BUCKET" in str(exc)
    else:
        raise AssertionError("Expected GCS artifact store construction to require a bucket.")


def test_agent_cloud_run_service_processes_pubsub_job(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'agent-service.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "agent-service-artifacts"))
    app_module = importlib.import_module("hound_forward.agent.service")

    app_module.build_runtime.cache_clear()
    client = TestClient(create_agent_service_app())
    service = app_module.build_runtime().service

    session = service.create_session(title="Agent service session")
    upload_video(service, session.session_id)
    agent_job = service.submit_agent_job(session_id=session.session_id, goal="Evaluate a Cloud Run agent request")

    response = client.post(
        "/pubsub/agent-jobs",
        json=encode_pubsub_job(
            Job(
                job_id=agent_job.job_id,
                job_type=agent_job.job_type.value,
                run_id=agent_job.run_id or "",
                session_id=agent_job.session_id,
                payload=agent_job.payload,
                metadata=agent_job.metadata,
            )
        ),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["result"]["run_status"] == "completed"


def test_worker_cloud_run_service_processes_pubsub_job(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HF_METADATA_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'worker-service.db'}")
    monkeypatch.setenv("HF_ARTIFACT_ROOT", str(tmp_path / "worker-service-artifacts"))
    app_module = importlib.import_module("hound_forward.worker.service")

    app_module.build_runtime.cache_clear()
    client = TestClient(create_worker_service_app())
    service = app_module.build_runtime().service

    session = service.create_session(title="Worker service session")
    video = upload_video(service, session.session_id)
    manifest = ExperimentManifestPlanner().plan("Evaluate worker service flow", dataset_video_ids=["video-001"])
    manifest.input_asset_ids = [video.asset.asset_id]
    run = service.create_run(session.session_id, manifest)
    service.enqueue_run(run.run_id)
    run_job = service.list_jobs(run_id=run.run_id)[0]

    response = client.post(
        "/pubsub/run-jobs",
        json=encode_pubsub_job(
            Job(
                job_id=run_job.job_id,
                job_type=run_job.job_type.value,
                run_id=run.run_id,
                session_id=session.session_id,
                payload=run_job.payload,
                metadata=run_job.metadata,
            )
        ),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run.run_id
    assert payload["status"] == "completed"
