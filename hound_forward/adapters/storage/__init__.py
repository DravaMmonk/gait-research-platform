from __future__ import annotations

from .local import LocalArtifactStore

try:
    from .azure_blob import AzureBlobArtifactStore
except ModuleNotFoundError:  # optional dependency
    AzureBlobArtifactStore = None

try:
    from .gcs import GCSArtifactStore
except ModuleNotFoundError:  # optional dependency
    GCSArtifactStore = None

__all__ = ["AzureBlobArtifactStore", "GCSArtifactStore", "LocalArtifactStore"]
