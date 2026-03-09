from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from gait_research_platform.core.config_loader import load_config
from gait_research_platform.core.data_manager import DataManager
from gait_research_platform.core.registry import registry
from gait_research_platform.utils.error_capture import format_exception_payload

# Import side effects register the concrete modules.
from gait_research_platform.analysis import clustering_analysis, embedding_visualization, periodicity_analysis  # noqa: F401
from gait_research_platform.experiments import anomaly_detection, contrastive_training, future_prediction  # noqa: F401
from gait_research_platform.representations import gait_phase_model, temporal_embedding  # noqa: F401
from gait_research_platform.signals import joint_angle_signal, pose_signal, velocity_signal  # noqa: F401


def _persistable_config(config: dict[str, Any]) -> dict[str, Any]:
    persistable = deepcopy(config)
    persistable.pop("_runtime", None)
    return persistable


def _build_manifest_entry(
    config: dict[str, Any],
    experiment_id: str,
    result_dir: str,
    status: str,
    metrics: dict[str, Any] | None,
    error: dict[str, Any] | None,
    data_manager: DataManager,
) -> dict[str, Any]:
    entry = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "experiment_name": config["experiment"]["name"],
        "config_path": config.get("_config_path"),
        "result_dir": result_dir,
        "signals": [signal["name"] for signal in config["signals"] if signal.get("enabled", True)],
        "representation": config["representation"]["model"],
        "metrics": metrics,
        "error": error,
    }
    entry.update(data_manager.get_git_metadata())
    return entry


def run_experiment(config: dict[str, Any]) -> dict[str, Any]:
    data_manager = DataManager(config)
    paths = data_manager.create_experiment_paths(config["experiment"].get("experiment_id", "auto"))
    logger, log_path = data_manager.create_logger(paths.root, f"gait_research_platform.{paths.experiment_id}")

    stage = "config"

    def set_stage(next_stage: str) -> None:
        nonlocal stage
        stage = next_stage
        logger.info("Stage changed to %s", next_stage)

    runtime_config = deepcopy(config)
    runtime_config["experiment"]["experiment_id"] = paths.experiment_id
    runtime_config["_runtime"] = {
        "experiment_id": paths.experiment_id,
        "result_dir": paths.root,
        "plots_dir": paths.plots,
        "artifacts_dir": paths.artifacts,
        "set_stage": set_stage,
        "logger": logger,
    }

    data_manager.save_experiment_config(paths.root, _persistable_config(runtime_config))
    logger.info("Starting experiment %s", paths.experiment_id)

    try:
        experiment_name = runtime_config["experiment"]["name"]
        experiment_cls = registry.get_from_category("experiments", experiment_name)
        experiment = experiment_cls()
        result = experiment.run(runtime_config)
        stage = "persistence"
        metrics = result.get("metrics")
        summary = result.get("summary") or {}
        summary.setdefault("status", "success")
        summary.setdefault("experiment_id", paths.experiment_id)
        summary.setdefault("artifacts", {})
        summary["log_path"] = str(log_path)

        data_manager.save_metrics(paths.root, metrics)
        data_manager.save_summary(paths.root, summary)
        data_manager.save_error(paths.root, None)

        manifest_entry = _build_manifest_entry(
            config=runtime_config,
            experiment_id=paths.experiment_id,
            result_dir=str(paths.root),
            status="success",
            metrics=metrics,
            error=None,
            data_manager=data_manager,
        )
        data_manager.append_manifest(manifest_entry)
        logger.info("Experiment completed successfully.")
        return {
            "experiment_id": paths.experiment_id,
            "status": "success",
            "result_dir": str(paths.root),
            "metrics": metrics,
            "summary": summary,
            "error": None,
        }
    except Exception as exc:
        error = format_exception_payload(exc, stage=stage)
        logger.exception("Experiment failed during stage %s", stage)
        data_manager.save_metrics(paths.root, None)
        summary = {
            "experiment_id": paths.experiment_id,
            "status": "failed",
            "artifacts": {
                "log_path": str(log_path),
            },
        }
        data_manager.save_summary(paths.root, summary)
        data_manager.save_error(paths.root, error)
        manifest_entry = _build_manifest_entry(
            config=runtime_config,
            experiment_id=paths.experiment_id,
            result_dir=str(paths.root),
            status="failed",
            metrics=None,
            error=error,
            data_manager=data_manager,
        )
        data_manager.append_manifest(manifest_entry)
        return {
            "experiment_id": paths.experiment_id,
            "status": "failed",
            "result_dir": str(paths.root),
            "metrics": None,
            "summary": summary,
            "error": error,
        }
    finally:
        data_manager.close_logger(logger)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a gait research experiment.")
    parser.add_argument("--config", required=True, help="Path to YAML config.")
    parser.add_argument("--print-result", action="store_true", help="Print the result summary as JSON.")
    args = parser.parse_args()

    config = load_config(args.config)
    result = run_experiment(config)
    if args.print_result:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
