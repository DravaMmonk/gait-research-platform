from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
import torch

from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.core.interfaces import Experiment
from gait_research_platform.core.registry import register_experiment, registry
from gait_research_platform.pipeline.build_signals import build_signals_for_video, concatenate_signals


@register_experiment("contrastive_training")
class ContrastiveTrainingExperiment(Experiment):
    name = "contrastive_training"

    def run(self, config: dict[str, Any]) -> dict[str, Any]:
        seed = int(config["experiment"].get("seed", 42))
        np.random.seed(seed)
        torch.manual_seed(seed)

        data_manager = DataManager(config)
        paths = data_manager.create_experiment_paths(config["experiment"].get("experiment_id", "auto"))
        config["experiment"]["experiment_id"] = paths.experiment_id
        data_manager.save_experiment_config(paths.root, config)

        manifest_entry = {
            "experiment_id": paths.experiment_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "experiment_name": self.name,
            "representation": config["representation"]["model"],
            "signals": [signal["name"] for signal in config["signals"] if signal.get("enabled", True)],
            "result_dir": str(paths.root),
            "metrics": {},
            "config_path": config.get("_config_path"),
        }
        manifest_entry.update(data_manager.get_git_metadata())

        try:
            video_ids = data_manager.list_video_ids()
            if not video_ids:
                raise ValueError("No video_ids available. Add pose parquet files or configure data.video_ids.")

            sequences: list[np.ndarray] = []
            for video_id in video_ids:
                signals = build_signals_for_video(video_id, config, data_manager)
                sequences.append(concatenate_signals(signals))

            input_dim = sequences[0].shape[1]
            representation_cls = registry.get_from_category("representations", config["representation"]["model"])
            representation_params = dict(config["representation"].get("params", {}))
            if representation_params.get("input_dim", "auto") == "auto":
                representation_params["input_dim"] = input_dim
            model = representation_cls(**representation_params)
            training_metrics = model.train(sequences, config)
            model.save(str(paths.artifacts))

            encoded = [model.encode(sequence) for sequence in sequences]
            embeddings_df = pd.DataFrame(encoded, columns=[f"dim_{index}" for index in range(len(encoded[0]))])
            embeddings_df.insert(0, "video_id", video_ids)
            embeddings_df.insert(1, "experiment_id", paths.experiment_id)

            experiment_embeddings_path = paths.root / "embeddings.parquet"
            embeddings_df.to_parquet(experiment_embeddings_path, index=False)
            data_manager.save_embeddings(paths.experiment_id, embeddings_df)

            metadata = pd.DataFrame({"video_id": video_ids, "experiment_id": paths.experiment_id})
            analysis_results: dict[str, Any] = {}
            for analysis_cfg in config.get("analysis", []):
                task_cls = registry.get_from_category("analysis", analysis_cfg["name"])
                task = task_cls(**analysis_cfg.get("params", {}))
                analysis_results[analysis_cfg["name"]] = task.run(
                    embeddings=embeddings_df,
                    metadata=metadata,
                    config=config,
                    output_dir=paths.plots,
                )

            metrics = {
                "final_loss": training_metrics["final_loss"],
                "num_sequences": training_metrics["num_sequences"],
                "embedding_dim": len(encoded[0]),
            }
            data_manager.save_metrics(paths.root, metrics)
            summary = {
                "experiment_id": paths.experiment_id,
                "video_ids": video_ids,
                "git": data_manager.get_git_metadata(),
                "analysis": analysis_results,
                "training": training_metrics,
                "artifacts": {
                    "model_path": str(paths.artifacts / "model.pt"),
                    "embeddings_path": str(experiment_embeddings_path),
                },
            }
            data_manager.save_summary(paths.root, summary)

            manifest_entry["status"] = "success"
            manifest_entry["metrics"] = metrics
            data_manager.append_manifest(manifest_entry)
            return {
                "experiment_id": paths.experiment_id,
                "result_dir": str(paths.root),
                "metrics": metrics,
                "summary": summary,
            }
        except Exception as exc:
            data_manager.save_metrics(paths.root, {"error": str(exc)})
            data_manager.save_summary(paths.root, {"error": str(exc)})
            manifest_entry["error"] = str(exc)
            data_manager.append_manifest(manifest_entry)
            raise
