from __future__ import annotations

from hound_forward.domain import AssetKind, AssetRecord, MetricDefinition, MetricResult, RunRecord
from hound_forward.ports import MetadataRepository, RunExecutor, ToolRunner


class PlatformRunExecutor(RunExecutor):
    """Execute agent-designed stage plans through the modular tool boundary."""

    def __init__(self, metadata: MetadataRepository, tool_runner: ToolRunner | None = None) -> None:
        self.metadata = metadata
        self.tool_runner = tool_runner

    def execute(self, run: RunRecord) -> tuple[dict, list[AssetRecord], list[MetricResult]]:
        if self.tool_runner is None:
            raise RuntimeError("Run execution requires a configured agent tool executor.")
        if not run.input_asset_ids:
            raise ValueError("Run execution requires at least one input asset.")
        if not run.execution_plan or not run.execution_plan.stages:
            raise ValueError("Run execution requires an execution plan.")

        current_asset = self._load_initial_asset(run)
        assets: list[AssetRecord] = []
        metric_results: list[MetricResult] = []
        summary: dict = {
            "run_id": run.run_id,
            "status": "completed",
            "execution_mode": "agent_tool_chain",
            "stage_count": len(run.execution_plan.stages),
        }
        for stage in run.execution_plan.stages:
            if stage.tool_invocation is None:
                continue
            input_asset = self._resolve_input_asset(
                run=run,
                current_asset=current_asset,
                input_asset_id=stage.tool_invocation.input_asset_id,
            )
            payload, asset = self.tool_runner.invoke(
                tool_name=stage.tool_invocation.tool_name,
                input_asset=input_asset,
                run_id=run.run_id,
                config=stage.tool_invocation.config,
            )
            assets.append(asset)
            current_asset = asset
            if asset.kind == AssetKind.METRIC_RESULT:
                metric_results.extend(self._register_metric_results(run=run, metrics_payload=payload, metrics_asset=asset))
            if isinstance(payload, dict) and payload.get("summary"):
                summary["last_stage_summary"] = payload["summary"]
        summary["tool_stage_count"] = len(assets)
        return summary, assets, metric_results

    def _load_initial_asset(self, run: RunRecord) -> AssetRecord:
        asset = self.metadata.get_asset(run.input_asset_ids[0])
        if asset is None:
            raise KeyError(f"Unknown input asset: {run.input_asset_ids[0]}")
        return asset

    def _resolve_input_asset(self, *, run: RunRecord, current_asset: AssetRecord, input_asset_id: str | None) -> AssetRecord:
        if input_asset_id is None:
            return current_asset
        if input_asset_id == current_asset.asset_id:
            return current_asset
        asset = self.metadata.get_asset(input_asset_id)
        if asset is None and input_asset_id in run.input_asset_ids:
            raise KeyError(f"Unknown input asset: {input_asset_id}")
        return asset or current_asset

    def _register_metric_results(
        self,
        *,
        run: RunRecord,
        metrics_payload: dict,
        metrics_asset: AssetRecord,
    ) -> list[MetricResult]:
        metric_values = metrics_payload.get("metrics") or {}
        definitions = {f"{item.name}:{item.version}": item for item in self.metadata.list_metric_definitions()}
        results: list[MetricResult] = []
        descriptions = {
            "stride_length": "Agent-computed stride length from the modular tool chain.",
            "asymmetry_index": "Agent-computed asymmetry index from the modular tool chain.",
            "gait_stability": "Agent-computed gait stability score from the modular tool chain.",
        }
        for name, value in metric_values.items():
            key = f"{name}:v1"
            definition = definitions.get(key)
            if definition is None:
                definition = self.metadata.register_metric_definition(
                    MetricDefinition(
                        name=name,
                        version="v1",
                        description=descriptions.get(name, f"Agent-computed metric {name}."),
                        config_schema={"type": "object", "agent_tool": True},
                    )
                )
            results.append(
                MetricResult(
                    run_id=run.run_id,
                    metric_definition_id=definition.metric_definition_id,
                    name=name,
                    version=definition.version,
                    value=float(value),
                    payload={"source_asset": metrics_asset.blob_path, "tool_chain": "agent_tools"},
                )
            )
        return results
