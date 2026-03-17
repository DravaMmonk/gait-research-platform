from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "v1"


def ensure_parent_dir(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def require_file(path: str | Path) -> Path:
    target = Path(path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(f"Required input file not found: {target}")
    return target


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(require_file(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    target = ensure_parent_dir(path)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return target

