from __future__ import annotations

from gait_research_platform.core.interfaces import Experiment
from gait_research_platform.core.registry import register_experiment


@register_experiment("future_prediction")
class FuturePredictionExperiment(Experiment):
    name = "future_prediction"

    def run(self, config: dict):
        del config
        raise NotImplementedError("future_prediction is reserved for a future extension.")
