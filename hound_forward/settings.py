from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MetadataSettings(BaseModel):
    database_url: str


class ArtifactStorageSettings(BaseModel):
    root: Path
    azure_blob_account_url: str | None
    azure_blob_container: str


class QueueSettings(BaseModel):
    backend: str
    azure_service_bus_namespace: str | None
    azure_service_bus_queue: str


class WorkerRuntimeSettings(BaseModel):
    default_runner: str
    placeholder_worker_mode: bool
    research_tool_execution_mode: str
    formula_evaluation_mode: str


class AgentRuntimeSettings(BaseModel):
    llm_model: str
    recursion_limit: int


class PlatformSettings(BaseSettings):
    """Runtime settings for local development and Azure deployment."""

    model_config = SettingsConfigDict(env_prefix="HF_", env_file=".env", extra="ignore")

    environment: str = "local"
    api_title: str = "Hound Forward Research Platform"

    metadata_database_url: str = "sqlite+pysqlite:///./.hf/local.db"
    artifact_root: Path = Field(default=Path(".hf/artifacts"))
    azure_blob_account_url: str | None = None
    azure_blob_container: str = "hound-platform"

    queue_backend: str = "in_memory"
    azure_service_bus_namespace: str | None = None
    azure_service_bus_queue: str = "runs"

    default_runner: str = "local"
    placeholder_worker_mode: bool = True
    research_tool_execution_mode: str = "local_function"
    formula_evaluation_mode: str = "scaffold"
    llm_model: str = "gpt-4o-mini"
    agent_recursion_limit: int = 12

    def artifact_root_path(self) -> Path:
        path = Path(self.artifact_root)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def metadata(self) -> MetadataSettings:
        return MetadataSettings(database_url=self.metadata_database_url)

    @property
    def artifact_storage(self) -> ArtifactStorageSettings:
        return ArtifactStorageSettings(
            root=self.artifact_root_path(),
            azure_blob_account_url=self.azure_blob_account_url,
            azure_blob_container=self.azure_blob_container,
        )

    @property
    def queue(self) -> QueueSettings:
        return QueueSettings(
            backend=self.queue_backend,
            azure_service_bus_namespace=self.azure_service_bus_namespace,
            azure_service_bus_queue=self.azure_service_bus_queue,
        )

    @property
    def worker_runtime(self) -> WorkerRuntimeSettings:
        return WorkerRuntimeSettings(
            default_runner=self.default_runner,
            placeholder_worker_mode=self.placeholder_worker_mode,
            research_tool_execution_mode=self.research_tool_execution_mode,
            formula_evaluation_mode=self.formula_evaluation_mode,
        )

    @property
    def agent_runtime(self) -> AgentRuntimeSettings:
        return AgentRuntimeSettings(llm_model=self.llm_model, recursion_limit=self.agent_recursion_limit)
