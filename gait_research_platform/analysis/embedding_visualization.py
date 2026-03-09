from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.manifold import TSNE

from gait_research_platform.core.interfaces import AnalysisTask
from gait_research_platform.core.registry import register_analysis
from gait_research_platform.utils.plotting_utils import save_current_figure


@register_analysis("embedding_visualization")
class EmbeddingVisualization(AnalysisTask):
    name = "embedding_visualization"

    def run(
        self,
        embeddings: pd.DataFrame,
        metadata: pd.DataFrame,
        config: dict[str, Any],
        output_dir: Path,
    ) -> dict[str, Any]:
        del config
        feature_columns = [column for column in embeddings.columns if column.startswith("dim_")]
        features = embeddings[feature_columns].to_numpy()
        method = self.params.get("method", "tsne")
        if method == "umap":
            try:
                import umap  # type: ignore
            except ImportError as exc:
                raise RuntimeError("UMAP requested but umap-learn is not installed.") from exc
            reducer = umap.UMAP(n_components=2, random_state=42)
            coords = reducer.fit_transform(features)
        else:
            perplexity = min(5, max(2, len(embeddings) - 1))
            reducer = TSNE(n_components=2, random_state=42, perplexity=perplexity)
            coords = reducer.fit_transform(features)

        viz_df = metadata.copy()
        viz_df["x"] = coords[:, 0]
        viz_df["y"] = coords[:, 1]
        coords_path = output_dir / "embedding_coords.parquet"
        viz_df.to_parquet(coords_path, index=False)

        sns.set_theme(style="whitegrid")
        plt.figure(figsize=(7, 5))
        sns.scatterplot(data=viz_df, x="x", y="y", hue="video_id", palette="tab10", s=80)
        plt.title("Embedding Visualization")
        plot_path = save_current_figure(output_dir / "embedding_visualization.png")
        return {
            "method": method,
            "plot_path": str(plot_path),
            "coords_path": str(coords_path),
        }
