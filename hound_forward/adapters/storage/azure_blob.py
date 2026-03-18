from __future__ import annotations

import hashlib
import json
from typing import Any

from hound_forward.domain import AssetKind, AssetRecord


class AzureBlobArtifactStore:
    """Persist artifacts to Azure Blob Storage and emit Azure-aligned asset metadata."""

    def __init__(self, *, container: str, account_url: str | None = None, connection_string: str | None = None) -> None:
        if not account_url and not connection_string:
            raise ValueError("AzureBlobArtifactStore requires either account_url or connection_string.")
        self.container = container
        self._service_client, self._container_client, resolved_account_url = self._build_clients(
            container=container,
            account_url=account_url,
            connection_string=connection_string,
        )
        self.account_url = resolved_account_url.rstrip("/")

    def put_json(self, run_id: str, name: str, payload: dict[str, Any], kind: str) -> AssetRecord:
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(encoded).hexdigest()
        blob_name = f"runs/{run_id}/{name}"
        self._upload_blob(blob_name=blob_name, content=encoded, mime_type="application/json")
        return AssetRecord(
            run_id=run_id,
            kind=AssetKind(kind),
            blob_path=f"{self.container}/{blob_name}",
            checksum=checksum,
            metadata={
                "storage_backend": "azure_blob",
                "account_url": self.account_url,
                "blob_uri": f"{self.account_url}/{self.container}/{blob_name}",
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
        metadata: dict | None = None,
    ) -> AssetRecord:
        checksum = hashlib.sha256(content).hexdigest()
        blob_name = f"sessions/{session_id}/{name}"
        self._upload_blob(blob_name=blob_name, content=content, mime_type=mime_type)
        return AssetRecord(
            session_id=session_id,
            kind=AssetKind(kind),
            blob_path=f"{self.container}/{blob_name}",
            checksum=checksum,
            mime_type=mime_type,
            metadata={
                "storage_backend": "azure_blob",
                "account_url": self.account_url,
                "blob_uri": f"{self.account_url}/{self.container}/{blob_name}",
                "file_name": name,
                **(metadata or {}),
            },
        )

    @staticmethod
    def _build_clients(*, container: str, account_url: str | None, connection_string: str | None):
        from azure.core.exceptions import ResourceExistsError
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        if connection_string:
            service_client = BlobServiceClient.from_connection_string(connection_string)
        else:
            service_client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
        container_client = service_client.get_container_client(container)
        try:
            container_client.create_container()
        except ResourceExistsError:
            pass
        resolved_account_url = account_url or service_client.url
        return service_client, container_client, resolved_account_url

    def _upload_blob(self, *, blob_name: str, content: bytes, mime_type: str) -> None:
        from azure.storage.blob import ContentSettings

        self._container_client.upload_blob(
            name=blob_name,
            data=content,
            overwrite=True,
            content_settings=ContentSettings(content_type=mime_type),
        )
