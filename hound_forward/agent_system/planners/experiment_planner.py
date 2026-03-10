from __future__ import annotations

from hound_forward.domain import AnalysisSpec, DatasetSelector, ExecutionPolicy, ExperimentManifest, MetricSpec, PipelineSpec


class ExperimentManifestPlanner:
    """Create config-driven manifests for the research platform."""

    def __init__(self, default_runner: str = "local") -> None:
        self.default_runner = default_runner

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
            tags=["azure", "research-platform", "agent-native"],
        )
