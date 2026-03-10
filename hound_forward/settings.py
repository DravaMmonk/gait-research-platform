from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlatformSettings(BaseSettings):
    """Runtime settings for local development and Azure deployment."""

    model_config = SettingsConfigDict(env_prefix="HF_", env_file=".env", extra="ignore")

    environment: str = "local"
    api_title: str = "Hound Forward Research Platform"

    metadata_database_url: str = "sqlite+pysqlite:///:memory:"
    artifact_root: Path = Field(default=Path(".hf/artifacts"))
    azure_blob_account_url: str | None = None
    azure_blob_container: str = "hound-platform"

    queue_backend: str = "in_memory"
    azure_service_bus_namespace: str | None = None
    azure_service_bus_queue: str = "runs"

    default_runner: str = "local"
    llm_model: str = "gpt-4o-mini"
    agent_recursion_limit: int = 12

    def artifact_root_path(self) -> Path:
        path = Path(self.artifact_root)
        path.mkdir(parents=True, exist_ok=True)
        return path
