from __future__ import annotations

import numpy as np

from gait_research_platform.core.interfaces import RepresentationModel
from gait_research_platform.core.registry import register_representation


@register_representation("gait_phase_model")
class GaitPhaseModel(RepresentationModel):
    def train(self, dataset, config):
        del dataset, config
        raise NotImplementedError("gait_phase_model is reserved for a future extension.")

    def encode(self, sequence: np.ndarray) -> np.ndarray:
        del sequence
        raise NotImplementedError("gait_phase_model is reserved for a future extension.")

    def save(self, output_dir: str) -> None:
        del output_dir
        raise NotImplementedError("gait_phase_model is reserved for a future extension.")

    @classmethod
    def load(cls, model_dir: str) -> "GaitPhaseModel":
        del model_dir
        raise NotImplementedError("gait_phase_model is reserved for a future extension.")
