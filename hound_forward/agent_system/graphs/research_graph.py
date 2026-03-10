from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from hound_forward.agent_system.planners.experiment_planner import ExperimentManifestPlanner
from hound_forward.agent_system.tools.registry import ToolRegistry


class ResearchGraphState(TypedDict, total=False):
    goal: str
    session_id: str
    manifest: dict
    run_id: str
    run_status: str
    run_data: dict
    metrics: dict
    recommendation: str


class ResearchGraph:
    def __init__(self, planner: ExperimentManifestPlanner, tools: ToolRegistry) -> None:
        self.planner = planner
        self.tools = tools
        self.graph = self._build_graph().compile()

    def invoke(self, goal: str, session_id: str) -> ResearchGraphState:
        return self.graph.invoke({"goal": goal, "session_id": session_id})

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(ResearchGraphState)
        graph.add_node("planner", self._planner_node)
        graph.add_node("create_run", self._create_run_node)
        graph.add_node("enqueue_run", self._enqueue_run_node)
        graph.add_node("monitor_run", self._monitor_run_node)
        graph.add_node("fetch_results", self._fetch_results_node)
        graph.add_node("analyze_results", self._analyze_results_node)
        graph.add_edge(START, "planner")
        graph.add_edge("planner", "create_run")
        graph.add_edge("create_run", "enqueue_run")
        graph.add_edge("enqueue_run", "monitor_run")
        graph.add_edge("monitor_run", "fetch_results")
        graph.add_edge("fetch_results", "analyze_results")
        graph.add_edge("analyze_results", END)
        return graph

    def _planner_node(self, state: ResearchGraphState) -> ResearchGraphState:
        manifest = self.planner.plan(goal=state["goal"])
        return {"manifest": manifest.model_dump(mode="json")}

    def _create_run_node(self, state: ResearchGraphState) -> ResearchGraphState:
        response = self.tools.call("create_run", session_id=state["session_id"], manifest=state["manifest"])
        return {"run_id": response.resource_id, "run_data": response.data}

    def _enqueue_run_node(self, state: ResearchGraphState) -> ResearchGraphState:
        response = self.tools.call("enqueue_run", run_id=state["run_id"])
        return {"run_status": response.status, "run_data": response.data}

    def _monitor_run_node(self, state: ResearchGraphState) -> ResearchGraphState:
        response = self.tools.call("get_run", run_id=state["run_id"])
        attempts = 0
        while response.status in {"queued", "running", "pending"} and attempts < 8:
            self.tools.service.process_next_job()
            response = self.tools.call("get_run", run_id=state["run_id"])
            attempts += 1
        return {"run_status": response.status, "run_data": response.data}

    def _fetch_results_node(self, state: ResearchGraphState) -> ResearchGraphState:
        metrics = self.tools.call("list_metrics", run_id=state["run_id"])
        return {"metrics": metrics.data}

    def _analyze_results_node(self, state: ResearchGraphState) -> ResearchGraphState:
        results = state.get("metrics", {}).get("results", [])
        metric_map = {item["name"]: item["value"] for item in results}
        recommendation = (
            "Increase dataset coverage and compare the latest run against a breed-specific cohort."
            if metric_map.get("asymmetry_index", 0) > 0.6
            else "Promote this manifest to a clinician review workflow and keep the metric definition stable."
        )
        return {"recommendation": recommendation}
