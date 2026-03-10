from __future__ import annotations

import hashlib
import json

from hound_forward.domain import AssetKind, AssetRecord


class AzureBlobArtifactStore:
    """Azure Blob artifact adapter that emits Azure-aligned asset metadata."""

    def __init__(self, account_url: str, container: str) -> None:
        self.account_url = account_url.rstrip("/")
        self.container = container

    def put_json(self, run_id: str, name: str, payload: dict, kind: str) -> AssetRecord:
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(encoded).hexdigest()
        blob_path = f"{self.container}/runs/{run_id}/{name}"
        return AssetRecord(
            run_id=run_id,
            kind=AssetKind(kind),
            blob_path=blob_path,
            checksum=checksum,
            metadata={
                "storage_backend": "azure_blob",
                "account_url": self.account_url,
                "blob_uri": f"{self.account_url}/{blob_path}",
            },
        )
