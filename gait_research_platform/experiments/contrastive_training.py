from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import torch

from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.core.interfaces import Experiment, ExperimentRunContext
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
        runtime = config.get("_runtime")
        if runtime is None:
            raise ValueError("Experiment runtime context is missing.")
        context = ExperimentRunContext(**runtime)

        context.logger.info("Starting experiment pipeline.")
        context.set_stage("signal")
        video_ids = data_manager.list_video_ids()
        if not video_ids:
            raise ValueError("No video_ids available. Add pose parquet files or configure data.video_ids.")

        sequences: list[np.ndarray] = []
        for video_id in video_ids:
            signals = build_signals_for_video(video_id, config, data_manager)
            sequences.append(concatenate_signals(signals))

        context.set_stage("training")
        input_dim = sequences[0].shape[1]
        representation_cls = registry.get_from_category("representations", config["representation"]["model"])
        representation_params = dict(config["representation"].get("params", {}))
        if representation_params.get("input_dim", "auto") == "auto":
            representation_params["input_dim"] = input_dim
        model = representation_cls(**representation_params)
        training_metrics = model.train(sequences, config)
        model.save(str(context.artifacts_dir))

        encoded = [model.encode(sequence) for sequence in sequences]
        embeddings_df = pd.DataFrame(encoded, columns=[f"dim_{index}" for index in range(len(encoded[0]))])
        embeddings_df.insert(0, "video_id", video_ids)
        embeddings_df.insert(1, "experiment_id", context.experiment_id)

        context.set_stage("persistence")
        experiment_embeddings_path = context.result_dir / "embeddings.parquet"
        embeddings_df.to_parquet(experiment_embeddings_path, index=False)
        data_manager.save_embeddings(context.experiment_id, embeddings_df)

        context.set_stage("analysis")
        metadata = pd.DataFrame({"video_id": video_ids, "experiment_id": context.experiment_id})
        analysis_results: dict[str, Any] = {}
        for analysis_cfg in config.get("analysis", []):
            task_cls = registry.get_from_category("analysis", analysis_cfg["name"])
            task = task_cls(**analysis_cfg.get("params", {}))
            analysis_results[analysis_cfg["name"]] = task.run(
                embeddings=embeddings_df,
                metadata=metadata,
                config=config,
                output_dir=context.plots_dir,
            )

        context.set_stage("persistence")
        metrics = {
            "final_loss": training_metrics["final_loss"],
            "num_sequences": training_metrics["num_sequences"],
            "embedding_dim": len(encoded[0]),
        }
        summary = {
            "experiment_id": context.experiment_id,
            "video_ids": video_ids,
            "git": data_manager.get_git_metadata(),
            "analysis": analysis_results,
            "training": training_metrics,
            "artifacts": {
                "model_path": str(context.artifacts_dir / "model.pt"),
                "embeddings_path": str(experiment_embeddings_path),
            },
        }
        return {
            "experiment_id": context.experiment_id,
            "metrics": metrics,
            "summary": summary,
            "artifacts": {
                "embeddings_path": str(experiment_embeddings_path),
                "model_path": str(context.artifacts_dir / "model.pt"),
            },
        }
