from __future__ import annotations

from hound_forward.domain import AssetRecord, DummyPipelineOutput, MetricDefinition, MetricResult, RunRecord
from hound_forward.ports import ArtifactStore, MetadataRepository, RunExecutor
from hound_forward.worker.pipeline.compute_fake_metrics import compute_fake_metrics
from hound_forward.worker.pipeline.generate_fake_keypoints import generate_fake_keypoints
from hound_forward.worker.pipeline.generate_report import generate_report


class DummyRuntimeValidationPipeline(RunExecutor):
    """Dummy runtime validation pipeline for one uploaded video -> one run -> one fake metric set."""

    def __init__(self, artifact_store: ArtifactStore, metadata: MetadataRepository) -> None:
        self.artifact_store = artifact_store
        self.metadata = metadata

    def execute(self, run: RunRecord) -> tuple[dict, list[AssetRecord], list[MetricResult]]:
        video_asset = self.load_video_asset(run)
        keypoints = self.generate_fake_keypoints(video_asset=video_asset, run=run)
        metrics = self.compute_fake_metrics(video_asset=video_asset, run=run, keypoints=keypoints)
        report = self.generate_report(video_asset=video_asset, run=run, metrics=metrics)
        output = DummyPipelineOutput(keypoints=keypoints, metrics=metrics, report=report)
        assets = self.write_outputs(run=run, output=output)
        metric_results = self.register_metric_results(run=run, metrics=metrics, metrics_asset=assets["metrics"])
        return report["summary"], [assets["keypoints"], assets["metrics"], assets["report"]], metric_results

    def load_video_asset(self, run: RunRecord) -> AssetRecord:
        if not run.input_asset_ids:
            raise ValueError("Dummy runtime validation requires one uploaded video asset.")
        asset = self.metadata.get_asset(run.input_asset_ids[0])
        if asset is None:
            raise KeyError(f"Unknown video asset: {run.input_asset_ids[0]}")
        if asset.kind.value != "video":
            raise ValueError(f"Input asset must be a video, received: {asset.kind.value}")
        return asset

    def generate_fake_keypoints(self, *, video_asset: AssetRecord, run: RunRecord) -> dict:
        return generate_fake_keypoints(video_asset=video_asset, run=run)

    def compute_fake_metrics(self, *, video_asset: AssetRecord, run: RunRecord, keypoints: dict) -> dict:
        return compute_fake_metrics(video_asset=video_asset, run=run, keypoints=keypoints)

    def generate_report(self, *, video_asset: AssetRecord, run: RunRecord, metrics: dict) -> dict:
        return generate_report(video_asset=video_asset, run=run, metrics=metrics)

    def write_outputs(self, *, run: RunRecord, output: DummyPipelineOutput) -> dict[str, AssetRecord]:
        keypoints_asset = self.artifact_store.put_json(run.run_id, "keypoints.json", output.keypoints, "keypoints")
        metrics_asset = self.artifact_store.put_json(run.run_id, "metrics.json", output.metrics, "metric_result")
        report_asset = self.artifact_store.put_json(run.run_id, "report.json", output.report, "report")
        return {"keypoints": keypoints_asset, "metrics": metrics_asset, "report": report_asset}

    def register_metric_results(self, *, run: RunRecord, metrics: dict, metrics_asset: AssetRecord) -> list[MetricResult]:
        definitions = {f"{item.name}:{item.version}": item for item in self.metadata.list_metric_definitions()}
        metric_results: list[MetricResult] = []
        default_metrics = [
            ("stride_length", metrics["stride_length"], "Fake stride length from the dummy runtime validation pipeline."),
            (
                "asymmetry_index",
                metrics["asymmetry_index"],
                "Fake asymmetry index from the dummy runtime validation pipeline.",
            ),
        ]
        for name, value, description in default_metrics:
            key = f"{name}:v1"
            definition = definitions.get(key)
            if definition is None:
                definition = self.metadata.register_metric_definition(
                    metric_definition=MetricDefinition(
                        name=name,
                        version="v1",
                        description=description,
                        config_schema={"type": "object", "properties": {}, "runtime_validation": True},
                    )
                )
            metric_results.append(
                MetricResult(
                    run_id=run.run_id,
                    metric_definition_id=definition.metric_definition_id,
                    name=name,
                    version=definition.version,
                    value=value,
                    payload={
                        "source_asset": metrics_asset.blob_path,
                        "placeholder_flags": {"dummy": True, "fake": True, "placeholder": True},
                    },
                )
            )
        return metric_results
