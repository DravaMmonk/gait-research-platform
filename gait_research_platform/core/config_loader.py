from __future__ import annotations

from pathlib import Path
from typing import Any

from omegaconf import DictConfig, OmegaConf


DEFAULT_CONFIG = {
    "experiment": {
        "name": "contrastive_training",
        "experiment_id": "auto",
        "seed": 42,
    },
    "data": {
        "root_dir": ".",
        "videos_dir": "gait_research_platform/data/videos",
        "poses_dir": "gait_research_platform/data/poses",
        "signals_dir": "gait_research_platform/data/signals",
        "embeddings_dir": "gait_research_platform/data/embeddings",
        "results_dir": "gait_research_platform/results",
        "manifest_path": "gait_research_platform/results/manifest.jsonl",
        "pose_extractor": None,
        "cache_signals": True,
        "video_ids": [],
    },
    "signals": [],
    "representation": {
        "model": "temporal_embedding",
        "params": {},
    },
    "training": {
        "method": "contrastive",
        "batch_size": 16,
        "epochs": 10,
        "learning_rate": 1e-3,
        "temperature": 0.1,
        "num_workers": 0,
    },
    "analysis": [],
    "agent": {
        "enabled": False,
        "provider": "openai_compatible",
        "model": "gpt-4o-mini",
    },
}


def _validate_required(config: dict[str, Any]) -> None:
    if not config["signals"]:
        raise ValueError("Config must define at least one signal")
    if not config["representation"]["model"]:
        raise ValueError("Config must define representation.model")
    if not config["experiment"]["name"]:
        raise ValueError("Config must define experiment.name")


def load_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    merged = OmegaConf.merge(OmegaConf.create(DEFAULT_CONFIG), OmegaConf.load(path))
    config = OmegaConf.to_container(merged, resolve=True)
    assert isinstance(config, dict)
    _validate_required(config)
    config["_config_path"] = str(path)
    return config


def merge_config(overrides: dict[str, Any] | DictConfig) -> dict[str, Any]:
    merged = OmegaConf.merge(OmegaConf.create(DEFAULT_CONFIG), overrides)
    config = OmegaConf.to_container(merged, resolve=True)
    assert isinstance(config, dict)
    _validate_required(config)
    return config


def save_config(config: dict[str, Any], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    OmegaConf.save(config=OmegaConf.create(config), f=path)
