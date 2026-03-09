from __future__ import annotations

import argparse
import json
from typing import Any

from gait_research_platform.core.config_loader import load_config, merge_config
from gait_research_platform.core.registry import registry

# Import side effects register the concrete modules.
from gait_research_platform.analysis import clustering_analysis, embedding_visualization, periodicity_analysis  # noqa: F401
from gait_research_platform.experiments import anomaly_detection, contrastive_training, future_prediction  # noqa: F401
from gait_research_platform.representations import gait_phase_model, temporal_embedding  # noqa: F401
from gait_research_platform.signals import joint_angle_signal, pose_signal, velocity_signal  # noqa: F401


def run_experiment(config: dict[str, Any]) -> dict[str, Any]:
    experiment_name = config["experiment"]["name"]
    experiment_cls = registry.get_from_category("experiments", experiment_name)
    experiment = experiment_cls()
    return experiment.run(config)


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
