from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from gait_research_platform.core.interfaces import AnalysisTask
from gait_research_platform.core.registry import register_analysis


@register_analysis("periodicity_analysis")
class PeriodicityAnalysis(AnalysisTask):
    name = "periodicity_analysis"

    def run(
        self,
        embeddings: pd.DataFrame,
        metadata: pd.DataFrame,
        config: dict[str, Any],
        output_dir: Path,
    ) -> dict[str, Any]:
        del embeddings, metadata, config, output_dir
        raise NotImplementedError("periodicity_analysis is reserved for a future extension.")
