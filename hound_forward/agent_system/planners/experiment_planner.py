from __future__ import annotations

from hound_forward.domain import (
    AnalysisSpec,
    DatasetSelector,
    ExecutionPlan,
    ExecutionPolicy,
    ExecutionStage,
    ExecutionStageType,
    ExperimentManifest,
    MetricSpec,
    PipelineSpec,
    ToolInvocationRecord,
)


class ExperimentManifestPlanner:
    """Create agent-oriented manifests and modular tool chains."""

    def __init__(self, default_runner: str = "local", available_tools: list[dict[str, str]] | None = None) -> None:
        self.default_runner = default_runner
        self.available_tools = {tool["name"]: tool for tool in (available_tools or [])}

    def plan(self, goal: str, dataset_video_ids: list[str] | None = None) -> ExperimentManifest:
        normalized_goal = goal.strip() or "Explore canine movement signals"
        slug = normalized_goal.lower().replace(" ", "-")[:48]
        return ExperimentManifest(
            name=f"research-{slug}",
            goal=normalized_goal,
            dataset=DatasetSelector(video_ids=dataset_video_ids or ["sample-video-001"]),
            pipeline=PipelineSpec(
                experiment_name="contrastive_training",
                keypoint_model="gait_pose_v3",
                signal_names=["velocity_signal", "pose_signal"],
                representation_model="temporal_embedding",
                parameters={"source": "planner", "goal": normalized_goal},
            ),
            metrics=[
                MetricSpec(name="gait_stability", version="v1"),
                MetricSpec(name="asymmetry_index", version="v1"),
            ],
            analysis=[AnalysisSpec(name="embedding_visualization", config={"method": "tsne"})],
            execution_policy=ExecutionPolicy(runner=self.default_runner, use_gpu=False),
            tags=["cloud", "research-platform", "agent-native"],
        )

    def plan_execution(self, goal: str, input_asset_ids: list[str] | None = None) -> ExecutionPlan:
        normalized_goal = goal.lower()
        tool_names: list[str]
        if "manifest" in normalized_goal:
            tool_names = ["visualize_pysr_manifest"]
        elif "formula" in normalized_goal:
            tool_names = ["decode_video", "extract_keypoints", "compute_gait_metrics", "generate_report"]
        else:
            tool_names = ["extract_keypoints", "compute_gait_metrics", "generate_report"]
            if "video" in normalized_goal and "decode_video" in self.available_tools:
                tool_names.insert(0, "decode_video")

        stages = [
            ExecutionStage(
                name=tool_name,
                stage_type=ExecutionStageType.AGENT_TOOL,
                tool_invocation=ToolInvocationRecord(
                    tool_name=tool_name,
                    input_asset_id=(
                        input_asset_ids[0]
                        if input_asset_ids
                        and (index == 0 or self.available_tools.get(tool_name, {}).get("input_kind") == "video")
                        else None
                    ),
                ),
                metadata={"planned_by": "langgraph", "goal": goal},
            )
            for index, tool_name in enumerate(tool_names)
            if tool_name in self.available_tools
        ]
        if not stages:
            raise ValueError("No compatible agent tools are available for planning.")
        return ExecutionPlan(stages=stages)
