from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def save_current_figure(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path
