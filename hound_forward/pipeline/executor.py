from __future__ import annotations

from hashlib import sha256

from hound_forward.domain import AssetRecord, MetricDefinition, MetricResult, RunRecord
from hound_forward.ports import ArtifactStore, MetadataRepository, RunExecutor


class DeterministicLocalRunExecutor(RunExecutor):
    """Deterministic local executor that produces Azure-aligned artifact and metric records."""

    def __init__(self, artifact_store: ArtifactStore, metadata: MetadataRepository) -> None:
        self.artifact_store = artifact_store
        self.metadata = metadata

    def execute(self, run: RunRecord) -> tuple[dict, list[AssetRecord], list[MetricResult]]:
        manifest = run.manifest
        summary_seed = sha256(f"{run.run_id}:{manifest.name}:{manifest.pipeline.experiment_name}".encode("utf-8")).hexdigest()
        score = (int(summary_seed[:8], 16) % 1000) / 1000
        dataset_size = max(1, len(manifest.dataset.video_ids) or len(manifest.dataset.session_ids) or len(manifest.dataset.dog_ids) or 1)
        gait_stability = round(0.5 + score / 2, 4)
        asymmetry_index = round(1 - gait_stability / 2, 4)
        summary = {
            "run_id": run.run_id,
            "manifest_id": manifest.id,
            "dataset_size": dataset_size,
            "pipeline": {
                "experiment_name": manifest.pipeline.experiment_name,
                "signals": manifest.pipeline.signal_names,
                "representation_model": manifest.pipeline.representation_model,
                "keypoint_model": manifest.pipeline.keypoint_model,
            },
            "status": "succeeded",
        }
        report_payload = {
            "summary": summary,
            "metrics": {
                "gait_stability": gait_stability,
                "asymmetry_index": asymmetry_index,
            },
            "analysis": [item.model_dump(mode="json") for item in manifest.analysis],
        }
        report_asset = self.artifact_store.put_json(run.run_id, "report.json", report_payload, "report")
        metrics_asset = self.artifact_store.put_json(run.run_id, "metrics.json", report_payload["metrics"], "metric_result")
        assets = [report_asset, metrics_asset]

        definitions = {f"{item.name}:{item.version}": item for item in self.metadata.list_metric_definitions()}
        metric_results: list[MetricResult] = []
        default_metrics = [
            ("gait_stability", gait_stability, "Deterministic stability score derived from the manifest."),
            ("asymmetry_index", asymmetry_index, "Deterministic asymmetry score derived from the manifest."),
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
                        config_schema={"type": "object", "properties": {}},
                    )
                )
            metric_results.append(
                MetricResult(
                    run_id=run.run_id,
                    metric_definition_id=definition.metric_definition_id,
                    name=name,
                    version=definition.version,
                    value=value,
                    payload={"dataset_size": dataset_size, "source_asset": metrics_asset.blob_path},
                )
            )
        return summary, assets, metric_results
