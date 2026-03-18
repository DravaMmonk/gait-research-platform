from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from hound_forward.agent_system.chat import ChatOrchestrator
from hound_forward.agent_system.planners import build_planner
from hound_forward.bootstrap import build_service as build_platform_service
from hound_forward.domain import (
    ChatRequest,
    ConsoleAgentRequest,
    ExecutionPlan,
    ExperimentManifest,
    FormulaStatus,
    JobType,
    ReviewEvidenceBundle,
    ReviewVerdict,
    RunKind,
)
from hound_forward.settings import PlatformSettings


class SessionCreateRequest(BaseModel):
    title: str
    dog_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class RunCreateRequest(BaseModel):
    session_id: str
    manifest: ExperimentManifest
    run_kind: RunKind = RunKind.PIPELINE
    execution_plan: ExecutionPlan | None = None


class AgentPlanRequest(BaseModel):
    session_id: str
    goal: str


class AgentJobCreateRequest(BaseModel):
    session_id: str
    goal: str
    user_id: str | None = None
    trace_id: str | None = None
    config: dict = Field(default_factory=dict)


class FormulaDefinitionCreateRequest(BaseModel):
    name: str
    version: str
    description: str
    status: FormulaStatus = FormulaStatus.DRAFT
    input_requirements: dict = Field(default_factory=dict)
    execution_spec: dict = Field(default_factory=dict)


class FormulaProposalCreateRequest(BaseModel):
    research_question: str
    proposal_payload: dict = Field(default_factory=dict)
    formula_definition_id: str | None = None
    source_run_id: str | None = None


class FormulaEvaluationCreateRequest(BaseModel):
    formula_definition_id: str
    run_id: str
    dataset_ref: str | None = None
    summary: dict = Field(default_factory=dict)


class FormulaReviewCreateRequest(BaseModel):
    formula_definition_id: str
    reviewer_id: str
    verdict: ReviewVerdict
    notes: str
    formula_evaluation_id: str | None = None
    evidence_bundle: dict = Field(default_factory=dict)


@lru_cache(maxsize=1)
def build_service():
    return build_platform_service()


@lru_cache(maxsize=1)
def build_chat_orchestrator() -> ChatOrchestrator:
    return ChatOrchestrator(service=build_service(), settings=PlatformSettings())


def create_app() -> FastAPI:
    app = FastAPI(title=PlatformSettings().api_title)
    service = build_service()
    chat_orchestrator = build_chat_orchestrator()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "hound-forward-api"}

    @app.post("/sessions")
    def create_session(request: SessionCreateRequest) -> dict:
        session = service.create_session(title=request.title, dog_id=request.dog_id, metadata=request.metadata)
        return session.model_dump(mode="json")

    @app.get("/sessions")
    def list_sessions() -> dict:
        return {"sessions": [item.model_dump(mode="json") for item in service.list_sessions()]}

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict:
        session = service.container.metadata.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.model_dump(mode="json")

    @app.delete("/sessions/{session_id}")
    def delete_session(session_id: str) -> dict:
        try:
            service.delete_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"session_id": session_id, "deleted": True}

    @app.post("/sessions/{session_id}/videos")
    async def upload_video(session_id: str, file: UploadFile = File(...)) -> dict:
        try:
            uploaded = service.upload_session_attachment(
                session_id=session_id,
                file_name=file.filename or "uploaded-video.mp4",
                content=await file.read(),
                mime_type=file.content_type or "video/mp4",
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return uploaded.model_dump(mode="json")

    @app.post("/sessions/{session_id}/attachments")
    async def upload_attachment(session_id: str, file: UploadFile = File(...)) -> dict:
        try:
            uploaded = service.upload_session_attachment(
                session_id=session_id,
                file_name=file.filename or "uploaded-attachment",
                content=await file.read(),
                mime_type=file.content_type or "application/octet-stream",
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return uploaded.model_dump(mode="json")

    @app.get("/sessions/{session_id}/attachments")
    def list_session_attachments(session_id: str, kind: str | None = None) -> dict:
        return {
            "session_id": session_id,
            "attachments": [item.model_dump(mode="json") for item in service.list_session_attachments(session_id, kind=kind)],
        }

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
            run = service.create_run(
                session_id=request.session_id,
                manifest=request.manifest,
                run_kind=request.run_kind,
                execution_plan=request.execution_plan,
            )
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

    @app.get("/runs/{run_id}/logs")
    def get_run_logs(run_id: str) -> dict:
        try:
            return service.get_run_logs(run_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/runs")
    def list_runs(session_id: str | None = None) -> dict:
        return {"runs": [item.model_dump(mode="json") for item in service.list_runs(session_id=session_id)]}

    @app.get("/jobs")
    def list_jobs(session_id: str | None = None, run_id: str | None = None, job_type: str | None = None) -> dict:
        resolved_type = JobType(job_type) if job_type else None
        return {
            "jobs": [
                item.model_dump(mode="json")
                for item in service.list_jobs(session_id=session_id, run_id=run_id, job_type=resolved_type)
            ]
        }

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str) -> dict:
        try:
            return service.get_job(job_id).model_dump(mode="json")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

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

    @app.post("/formulas/definitions")
    def create_formula_definition(request: FormulaDefinitionCreateRequest) -> dict:
        record = service.create_formula_definition(
            name=request.name,
            version=request.version,
            description=request.description,
            input_requirements=request.input_requirements,
            execution_spec=request.execution_spec,
            status=request.status,
        )
        return record.model_dump(mode="json")

    @app.get("/formulas/definitions")
    def list_formula_definitions() -> dict:
        return {"definitions": [item.model_dump(mode="json") for item in service.list_formula_definitions()]}

    @app.get("/formulas/definitions/{formula_definition_id}")
    def get_formula_definition(formula_definition_id: str) -> dict:
        try:
            return service.get_formula_definition(formula_definition_id).model_dump(mode="json")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/formulas/proposals")
    def create_formula_proposal(request: FormulaProposalCreateRequest) -> dict:
        proposal = service.create_formula_proposal(
            research_question=request.research_question,
            proposal_payload=request.proposal_payload,
            formula_definition_id=request.formula_definition_id,
            source_run_id=request.source_run_id,
        )
        return proposal.model_dump(mode="json")

    @app.get("/formulas/proposals")
    def list_formula_proposals(formula_definition_id: str | None = None) -> dict:
        return {"proposals": [item.model_dump(mode="json") for item in service.list_formula_proposals(formula_definition_id)]}

    @app.post("/formulas/evaluations")
    def create_formula_evaluation(request: FormulaEvaluationCreateRequest) -> dict:
        evaluation = service.create_formula_evaluation(
            formula_definition_id=request.formula_definition_id,
            run_id=request.run_id,
            dataset_ref=request.dataset_ref,
            summary=request.summary,
        )
        return evaluation.model_dump(mode="json")

    @app.get("/formulas/evaluations")
    def list_formula_evaluations(formula_definition_id: str | None = None) -> dict:
        return {"evaluations": [item.model_dump(mode="json") for item in service.list_formula_evaluations(formula_definition_id)]}

    @app.post("/formulas/reviews")
    def create_formula_review(request: FormulaReviewCreateRequest) -> dict:
        review = service.create_formula_review(
            formula_definition_id=request.formula_definition_id,
            reviewer_id=request.reviewer_id,
            verdict=request.verdict,
            notes=request.notes,
            formula_evaluation_id=request.formula_evaluation_id,
            evidence_bundle=ReviewEvidenceBundle.model_validate(request.evidence_bundle),
        )
        return review.model_dump(mode="json")

    @app.get("/formulas/reviews")
    def list_formula_reviews(formula_definition_id: str | None = None) -> dict:
        return {"reviews": [item.model_dump(mode="json") for item in service.list_formula_reviews(formula_definition_id)]}

    @app.post("/agent/plan")
    def agent_plan(request: AgentPlanRequest) -> dict:
        planner = build_planner(
            settings=PlatformSettings(),
            available_tools=service.container.tool_runner.describe_tools() if service.container.tool_runner else [],
        )
        manifest = planner.plan(goal=request.goal)
        execution_plan = planner.plan_execution(goal=request.goal)
        return {"manifest": manifest.model_dump(mode="json"), "execution_plan": execution_plan.model_dump(mode="json")}

    @app.post("/agent/execute-plan")
    def agent_execute_plan(request: AgentJobCreateRequest) -> dict:
        try:
            job = service.submit_agent_job(
                session_id=request.session_id,
                goal=request.goal,
                user_id=request.user_id,
                trace_id=request.trace_id,
                config=request.config,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return job.model_dump(mode="json")

    @app.post("/api/chat")
    def api_chat(request: ChatRequest) -> dict:
        try:
            response = chat_orchestrator.handle(
                session_id=request.session_id,
                message=request.message,
                context=request.context,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return response.model_dump(mode="json")

    @app.post("/agent/console/respond")
    def agent_console_respond(request: ConsoleAgentRequest) -> dict:
        try:
            response = service.respond_to_console(
                session_id=request.session_id,
                message=request.message,
                display_preferences=request.display_preferences,
                active_context=request.active_context,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return response.model_dump(mode="json")

    return app


app = create_app()
