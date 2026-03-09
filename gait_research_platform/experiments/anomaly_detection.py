from __future__ import annotations

from gait_research_platform.core.interfaces import Experiment
from gait_research_platform.core.registry import register_experiment


@register_experiment("anomaly_detection")
class AnomalyDetectionExperiment(Experiment):
    name = "anomaly_detection"

    def run(self, config: dict):
        del config
        raise NotImplementedError("anomaly_detection is reserved for a future extension.")
