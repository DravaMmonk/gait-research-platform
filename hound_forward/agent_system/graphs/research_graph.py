from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from hound_forward.agent_system.planners.experiment_planner import ExperimentManifestPlanner
from hound_forward.agent_system.tools.registry import ToolRegistry
from hound_forward.worker.runtime import PlaceholderLocalWorkerBridge


class ResearchGraphState(TypedDict, total=False):
    goal: str
    session_id: str
    manifest: dict
    video_asset_id: str
    run_id: str
    run_status: str
    run_data: dict
    metrics: dict
    recommendation: str


class ResearchGraph:
    def __init__(
        self,
        planner: ExperimentManifestPlanner,
        tools: ToolRegistry,
        worker_bridge: PlaceholderLocalWorkerBridge | None = None,
    ) -> None:
        self.planner = planner
        self.tools = tools
        self.worker_bridge = worker_bridge or PlaceholderLocalWorkerBridge(service=tools.service)
        self.graph = self._build_graph().compile()

    def invoke(self, goal: str, session_id: str) -> ResearchGraphState:
        return self.graph.invoke({"goal": goal, "session_id": session_id})

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(ResearchGraphState)
        graph.add_node("planner", self._planner_node)
        graph.add_node("select_video_asset", self._select_video_asset_node)
        graph.add_node("create_run", self._create_run_node)
        graph.add_node("enqueue_run", self._enqueue_run_node)
        graph.add_node("monitor_run", self._monitor_run_node)
        graph.add_node("fetch_results", self._fetch_results_node)
        graph.add_node("analyze_results", self._analyze_results_node)
        graph.add_edge(START, "planner")
        graph.add_edge("planner", "select_video_asset")
        graph.add_edge("select_video_asset", "create_run")
        graph.add_edge("create_run", "enqueue_run")
        graph.add_edge("enqueue_run", "monitor_run")
        graph.add_edge("monitor_run", "fetch_results")
        graph.add_edge("fetch_results", "analyze_results")
        graph.add_edge("analyze_results", END)
        return graph

    def _planner_node(self, state: ResearchGraphState) -> ResearchGraphState:
        manifest = self.planner.plan(goal=state["goal"])
        return {"manifest": manifest.model_dump(mode="json")}

    def _select_video_asset_node(self, state: ResearchGraphState) -> ResearchGraphState:
        response = self.tools.call("list_session_videos", session_id=state["session_id"])
        videos = response.data.get("videos", [])
        if not videos:
            raise ValueError("Runtime validation mode requires one uploaded video before agent execution.")
        manifest = dict(state["manifest"])
        manifest["input_asset_ids"] = [videos[0]["asset_id"]]
        return {"manifest": manifest, "video_asset_id": videos[0]["asset_id"]}

    def _create_run_node(self, state: ResearchGraphState) -> ResearchGraphState:
        response = self.tools.call("create_run", session_id=state["session_id"], manifest=state["manifest"])
        return {"run_id": response.resource_id, "run_data": response.data}

    def _enqueue_run_node(self, state: ResearchGraphState) -> ResearchGraphState:
        response = self.tools.call("enqueue_run", run_id=state["run_id"])
        return {"run_status": response.status, "run_data": response.data}

    def _monitor_run_node(self, state: ResearchGraphState) -> ResearchGraphState:
        response = self.tools.call("get_run", run_id=state["run_id"])
        attempts = 0
        while response.status in {"queued", "running", "created"} and attempts < 8:
            self.worker_bridge.drain_once()
            response = self.tools.call("get_run", run_id=state["run_id"])
            attempts += 1
        return {"run_status": response.status, "run_data": response.data}

    def _fetch_results_node(self, state: ResearchGraphState) -> ResearchGraphState:
        metrics = self.tools.call("read_metrics", run_id=state["run_id"])
        return {"metrics": metrics.data}

    def _analyze_results_node(self, state: ResearchGraphState) -> ResearchGraphState:
        results = state.get("metrics", {}).get("metric_results", [])
        metric_map = {item["name"]: item["value"] for item in results}
        recommendation = (
            "Dummy runtime validation result: compare this fake asymmetry score against another uploaded video before connecting a real CV model."
            if metric_map.get("asymmetry_index", 0) > 0.6
            else "Dummy runtime validation result: the fake metrics are stable enough to proceed to a real worker integration test with the same run contract."
        )
        return {"recommendation": recommendation}
