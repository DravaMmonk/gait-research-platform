from __future__ import annotations

from hound_forward.domain import AssetRecord, MetricResult, RunKind, RunRecord
from hound_forward.pipeline.dummy_pipeline import DummyRuntimeValidationPipeline
from hound_forward.ports import RunExecutor, ToolRunner


class PlatformRunExecutor(RunExecutor):
    """Dispatch runtime validation runs and staged research-tool runs through one executor boundary."""

    def __init__(self, dummy_pipeline: DummyRuntimeValidationPipeline, tool_runner: ToolRunner | None = None) -> None:
        self.dummy_pipeline = dummy_pipeline
        self.tool_runner = tool_runner

    def execute(self, run: RunRecord) -> tuple[dict, list[AssetRecord], list[MetricResult]]:
        if run.run_kind != RunKind.FORMULA_EVALUATION:
            return self.dummy_pipeline.execute(run)
        return self._execute_formula_evaluation(run)

    def _execute_formula_evaluation(self, run: RunRecord) -> tuple[dict, list[AssetRecord], list[MetricResult]]:
        if self.tool_runner is None:
            raise RuntimeError("Formula evaluation execution requires a configured tool runner.")
        if not run.input_asset_ids:
            raise ValueError("Formula evaluation run requires at least one input asset.")
        if not run.execution_plan or not run.execution_plan.stages:
            raise ValueError("Formula evaluation run requires an execution plan.")
        video_asset = self.dummy_pipeline.load_video_asset(run)
        assets: list[AssetRecord] = []
        for stage in run.execution_plan.stages:
            if stage.tool_invocation is None:
                continue
            _, asset = self.tool_runner.invoke(
                tool_name=stage.tool_invocation.tool_name,
                input_asset=video_asset,
                run_id=run.run_id,
                config=stage.tool_invocation.config,
            )
            assets.append(asset)
        summary = {
            "run_id": run.run_id,
            "status": "completed",
            "execution_mode": "formula_evaluation_scaffold",
            "tool_stage_count": len(assets),
            "placeholder_flags": {"dummy": False, "fake": False, "placeholder": True},
        }
        return summary, assets, []
