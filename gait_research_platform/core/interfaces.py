from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


class PoseExtractor(ABC):
    """Build pose data from a raw video asset."""

    name: str = "pose_extractor"

    @abstractmethod
    def extract(self, video_path: Path) -> pd.DataFrame:
        raise NotImplementedError


class Signal(ABC):
    """Convert pose data into a T x F motion feature matrix."""

    name: str

    def __init__(self, **params: Any) -> None:
        self.params = params

    @abstractmethod
    def build(self, video_id: str, pose_data: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError


class RepresentationModel(ABC):
    """Train and encode motion sequences."""

    @abstractmethod
    def train(self, dataset: Any, config: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def encode(self, sequence: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def save(self, output_dir: str) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def load(cls, model_dir: str) -> "RepresentationModel":
        raise NotImplementedError


class Experiment(ABC):
    """Run a research experiment pipeline."""

    name: str

    @abstractmethod
    def run(self, config: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class AnalysisTask(ABC):
    """Run post-hoc analysis over embeddings and metadata."""

    name: str

    def __init__(self, **params: Any) -> None:
        self.params = params

    @abstractmethod
    def run(
        self,
        embeddings: pd.DataFrame,
        metadata: pd.DataFrame,
        config: dict[str, Any],
        output_dir: Path,
    ) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class ExperimentRunContext:
    experiment_id: str
    result_dir: Path
    plots_dir: Path
    artifacts_dir: Path
    set_stage: Any
    logger: Any
