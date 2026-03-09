from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd

from gait_research_platform.core.config_loader import save_config
from gait_research_platform.core.registry import registry


@dataclass
class ExperimentPaths:
    experiment_id: str
    root: Path
    plots: Path
    artifacts: Path


class NullPoseExtractor:
    name = "null_pose_extractor"

    def extract(self, video_path: Path) -> pd.DataFrame:
        raise FileNotFoundError(
            f"Pose file missing for video '{video_path.stem}'. "
            "No pose extractor configured. Add parquet pose files or register a PoseExtractor."
        )


class DataManager:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        data_config = config["data"]
        self.root_dir = Path(data_config.get("root_dir", ".")).resolve()
        self.videos_dir = self.root_dir / data_config["videos_dir"]
        self.poses_dir = self.root_dir / data_config["poses_dir"]
        self.signals_dir = self.root_dir / data_config["signals_dir"]
        self.embeddings_dir = self.root_dir / data_config["embeddings_dir"]
        self.results_dir = self.root_dir / data_config["results_dir"]
        self.manifest_path = self.root_dir / data_config["manifest_path"]

        for path in (
            self.videos_dir,
            self.poses_dir,
            self.signals_dir,
            self.embeddings_dir,
            self.results_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def list_video_ids(self) -> list[str]:
        configured = self.config["data"].get("video_ids", [])
        if configured:
            return list(configured)
        return sorted(path.stem for path in self.poses_dir.glob("*.parquet"))

    def video_path(self, video_id: str) -> Path:
        return self.videos_dir / f"{video_id}.mp4"

    def pose_path(self, video_id: str) -> Path:
        return self.poses_dir / f"{video_id}.parquet"

    def signal_path(self, video_id: str, signal_name: str) -> Path:
        return self.signals_dir / f"{video_id}_{signal_name}.parquet"

    def embedding_path(self, experiment_id: str) -> Path:
        return self.embeddings_dir / f"{experiment_id}.parquet"

    def load_pose(self, video_id: str) -> pd.DataFrame:
        return pd.read_parquet(self.pose_path(video_id))

    def save_pose(self, video_id: str, pose_data: pd.DataFrame) -> Path:
        path = self.pose_path(video_id)
        pose_data.to_parquet(path, index=False)
        return path

    def ensure_pose(self, video_id: str) -> pd.DataFrame:
        path = self.pose_path(video_id)
        if path.exists():
            return pd.read_parquet(path)

        extractor_name = self.config["data"].get("pose_extractor")
        if extractor_name:
            extractor_cls = registry.get_from_category("pose_extractors", extractor_name)
            extractor = extractor_cls()
        else:
            extractor = NullPoseExtractor()
        pose_data = extractor.extract(self.video_path(video_id))
        return pose_data

    def load_signal(self, video_id: str, signal_name: str) -> pd.DataFrame:
        return pd.read_parquet(self.signal_path(video_id, signal_name))

    def save_signal(self, video_id: str, signal_name: str, features: np.ndarray) -> Path:
        path = self.signal_path(video_id, signal_name)
        frame_index = np.arange(features.shape[0], dtype=int)
        frame = pd.DataFrame(features)
        frame.insert(0, "frame_index", frame_index)
        frame.insert(0, "signal_name", signal_name)
        frame.insert(0, "video_id", video_id)
        frame.to_parquet(path, index=False)
        return path

    def create_experiment_paths(self, experiment_id: str | None = None) -> ExperimentPaths:
        if experiment_id in (None, "", "auto"):
            experiment_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
        root = self.results_dir / experiment_id
        plots = root / "plots"
        artifacts = root / "artifacts"
        plots.mkdir(parents=True, exist_ok=True)
        artifacts.mkdir(parents=True, exist_ok=True)
        return ExperimentPaths(experiment_id=experiment_id, root=root, plots=plots, artifacts=artifacts)

    def save_embeddings(self, experiment_id: str, embeddings: pd.DataFrame) -> Path:
        path = self.embedding_path(experiment_id)
        embeddings.to_parquet(path, index=False)
        return path

    def save_metrics(self, experiment_dir: Path, metrics: dict[str, Any] | None) -> Path:
        path = experiment_dir / "metrics.json"
        path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return path

    def save_summary(self, experiment_dir: Path, summary: dict[str, Any]) -> Path:
        path = experiment_dir / "summary.json"
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return path

    def save_experiment_config(self, experiment_dir: Path, config: dict[str, Any]) -> Path:
        path = experiment_dir / "config.yaml"
        save_config(config, path)
        return path

    def save_error(self, experiment_dir: Path, error: dict[str, Any] | None) -> Path:
        path = experiment_dir / "error.json"
        path.write_text(json.dumps(error, indent=2), encoding="utf-8")
        return path

    def load_error(self, experiment_dir: Path) -> dict[str, Any] | None:
        path = experiment_dir / "error.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def load_metrics(self, experiment_dir: Path) -> dict[str, Any] | None:
        path = experiment_dir / "metrics.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def load_summary(self, experiment_dir: Path) -> dict[str, Any] | None:
        path = experiment_dir / "summary.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def result_dir(self, experiment_id: str) -> Path:
        return self.results_dir / experiment_id

    def create_logger(self, experiment_dir: Path, logger_name: str) -> tuple[logging.Logger, Path]:
        log_path = experiment_dir / "logs.txt"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.handlers = []
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        return logger, log_path

    def close_logger(self, logger: logging.Logger) -> None:
        for handler in list(logger.handlers):
            handler.flush()
            handler.close()
            logger.removeHandler(handler)

    def append_manifest(self, entry: dict[str, Any]) -> None:
        with self.manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

    def read_manifest(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.manifest_path.exists():
            return []
        lines = self.manifest_path.read_text(encoding="utf-8").splitlines()
        if limit is not None:
            lines = lines[-limit:]
        return [json.loads(line) for line in lines if line.strip()]

    def get_git_metadata(self) -> dict[str, Any]:
        try:
            commit = (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.root_dir,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                .strip()
            )
        except Exception:
            commit = None

        try:
            branch = (
                subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.root_dir,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                .strip()
            )
        except Exception:
            branch = None
        return {"git_commit": commit, "git_branch": branch}
