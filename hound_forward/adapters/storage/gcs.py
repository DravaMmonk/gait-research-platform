from __future__ import annotations

import hashlib
import json
from typing import Any

from hound_forward.domain import AssetKind, AssetRecord


class GCSArtifactStore:
    """Persist artifacts to Google Cloud Storage using a pre-provisioned bucket."""

    def __init__(self, *, bucket: str, project_id: str | None = None, endpoint: str | None = None) -> None:
        if not bucket:
            raise ValueError("GCSArtifactStore requires a bucket name.")
        self.bucket_name = bucket
        self.project_id = project_id
        self.endpoint = endpoint
        self._client, self._bucket = self._build_clients(bucket=bucket, project_id=project_id, endpoint=endpoint)

    def put_json(self, run_id: str, name: str, payload: dict[str, Any], kind: str) -> AssetRecord:
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(encoded).hexdigest()
        object_name = f"runs/{run_id}/{name}"
        self._upload_blob(object_name=object_name, content=encoded, mime_type="application/json")
        return AssetRecord(
            run_id=run_id,
            kind=AssetKind(kind),
            blob_path=f"{self.bucket_name}/{object_name}",
            checksum=checksum,
            metadata={
                "storage_backend": "gcs",
                "bucket": self.bucket_name,
                "gcs_uri": f"gs://{self.bucket_name}/{object_name}",
                "file_name": name,
            },
        )

    def put_bytes(
        self,
        *,
        session_id: str,
        name: str,
        content: bytes,
        kind: str,
        mime_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> AssetRecord:
        checksum = hashlib.sha256(content).hexdigest()
        object_name = f"sessions/{session_id}/{name}"
        self._upload_blob(object_name=object_name, content=content, mime_type=mime_type)
        return AssetRecord(
            session_id=session_id,
            kind=AssetKind(kind),
            blob_path=f"{self.bucket_name}/{object_name}",
            checksum=checksum,
            mime_type=mime_type,
            metadata={
                "storage_backend": "gcs",
                "bucket": self.bucket_name,
                "gcs_uri": f"gs://{self.bucket_name}/{object_name}",
                "file_name": name,
                **(metadata or {}),
            },
        )

    @staticmethod
    def _build_clients(*, bucket: str, project_id: str | None, endpoint: str | None):
        from google.cloud import storage

        client_options = {"api_endpoint": endpoint} if endpoint else None
        client = storage.Client(project=project_id, client_options=client_options)
        return client, client.bucket(bucket)

    def _upload_blob(self, *, object_name: str, content: bytes, mime_type: str) -> None:
        blob = self._bucket.blob(object_name)
        blob.upload_from_string(content, content_type=mime_type)
