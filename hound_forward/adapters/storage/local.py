from __future__ import annotations

import hashlib
import json
from pathlib import Path

from hound_forward.domain import AssetKind, AssetRecord


class LocalArtifactStore:
    """Persist run artifacts on the local filesystem using the same asset contract as Azure Blob."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put_json(self, run_id: str, name: str, payload: dict, kind: str) -> AssetRecord:
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / name
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        path.write_bytes(encoded)
        checksum = hashlib.sha256(encoded).hexdigest()
        return AssetRecord(
            run_id=run_id,
            kind=AssetKind(kind),
            blob_path=str(path),
            checksum=checksum,
            metadata={"storage_backend": "local", "file_name": name},
        )
