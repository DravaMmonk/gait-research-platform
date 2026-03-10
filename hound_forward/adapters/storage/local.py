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

    def put_bytes(
        self,
        *,
        session_id: str,
        name: str,
        content: bytes,
        kind: str,
        mime_type: str,
        metadata: dict | None = None,
    ) -> AssetRecord:
        session_dir = self.root / "sessions" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        path = session_dir / name
        path.write_bytes(content)
        checksum = hashlib.sha256(content).hexdigest()
        return AssetRecord(
            session_id=session_id,
            kind=AssetKind(kind),
            blob_path=str(path),
            checksum=checksum,
            mime_type=mime_type,
            metadata={"storage_backend": "local", "file_name": name, **(metadata or {})},
        )
