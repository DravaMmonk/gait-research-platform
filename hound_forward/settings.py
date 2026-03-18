from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MetadataSettings(BaseModel):
    database_url: str


class ArtifactStorageSettings(BaseModel):
    backend: str
    root: Path
    azure_blob_account_url: str | None
    azure_blob_connection_string: str | None
    azure_blob_container: str
    gcp_project_id: str | None
    gcs_bucket: str | None
    gcs_endpoint: str | None


class QueueEndpointSettings(BaseModel):
    name: str
    topic: str
    subscription: str | None = None


class QueueSettings(BaseModel):
    backend: str
    poll_interval_seconds: float
    azure_service_bus_namespace: str | None
    gcp_project_id: str | None
    gcp_pubsub_endpoint: str | None
    run: QueueEndpointSettings
    agent: QueueEndpointSettings


class WorkerRuntimeSettings(BaseModel):
    default_runner: str
    placeholder_worker_mode: bool
    research_tool_execution_mode: str
    formula_evaluation_mode: str
    poll_interval_seconds: float
    max_idle_polls: int
    max_runs_per_invocation: int


class AgentRuntimeSettings(BaseModel):
    llm_model: str
    recursion_limit: int
    planner_mode: str


class PlatformSettings(BaseSettings):
    """Runtime settings for local development and Azure deployment."""

    model_config = SettingsConfigDict(env_prefix="HF_", env_file=".env", extra="ignore")

    environment: str = "local"
    api_title: str = "Hound Forward Research Platform"

    metadata_database_url: str = "sqlite+pysqlite:///./.hf/local.db"
    artifact_backend: str = "local"
    artifact_root: Path = Field(default=Path(".hf/artifacts"))
    azure_blob_account_url: str | None = None
    azure_blob_connection_string: str | None = None
    azure_blob_container: str = "hound-platform"
    gcp_project_id: str | None = None
    gcp_storage_bucket: str | None = None
    gcp_storage_endpoint: str | None = None

    queue_backend: str = "in_memory"
    azure_service_bus_namespace: str | None = None
    queue_run_name: str = "runs"
    queue_agent_name: str = "agent-runs"
    azure_service_bus_run_queue: str | None = None
    azure_service_bus_agent_queue: str | None = None
    gcp_pubsub_endpoint: str | None = None
    gcp_pubsub_run_topic: str | None = None
    gcp_pubsub_run_subscription: str | None = None
    gcp_pubsub_agent_topic: str | None = None
    gcp_pubsub_agent_subscription: str | None = None
    queue_poll_interval_seconds: float = 1.0

    default_runner: str = "local"
    placeholder_worker_mode: bool = True
    research_tool_execution_mode: str = "local_function"
    formula_evaluation_mode: str = "scaffold"
    worker_max_idle_polls: int = 3
    worker_max_runs_per_invocation: int = 20
    llm_model: str = "gpt-4o-mini"
    agent_recursion_limit: int = 12
    planner_mode: str = "hybrid"

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
            backend=self.artifact_backend,
            root=self.artifact_root_path(),
            azure_blob_account_url=self.azure_blob_account_url,
            azure_blob_connection_string=self.azure_blob_connection_string,
            azure_blob_container=self.azure_blob_container,
            gcp_project_id=self.gcp_project_id,
            gcs_bucket=self.gcp_storage_bucket,
            gcs_endpoint=self.gcp_storage_endpoint,
        )

    @property
    def queue(self) -> QueueSettings:
        return QueueSettings(
            backend=self.queue_backend,
            poll_interval_seconds=self.queue_poll_interval_seconds,
            azure_service_bus_namespace=self.azure_service_bus_namespace,
            gcp_project_id=self.gcp_project_id,
            gcp_pubsub_endpoint=self.gcp_pubsub_endpoint,
            run=QueueEndpointSettings(
                name=self.queue_run_name,
                topic=self.gcp_pubsub_run_topic or self.azure_service_bus_run_queue or self.queue_run_name,
                subscription=self.gcp_pubsub_run_subscription,
            ),
            agent=QueueEndpointSettings(
                name=self.queue_agent_name,
                topic=self.gcp_pubsub_agent_topic or self.azure_service_bus_agent_queue or self.queue_agent_name,
                subscription=self.gcp_pubsub_agent_subscription,
            ),
        )

    @property
    def worker_runtime(self) -> WorkerRuntimeSettings:
        return WorkerRuntimeSettings(
            default_runner=self.default_runner,
            placeholder_worker_mode=self.placeholder_worker_mode,
            research_tool_execution_mode=self.research_tool_execution_mode,
            formula_evaluation_mode=self.formula_evaluation_mode,
            poll_interval_seconds=self.queue_poll_interval_seconds,
            max_idle_polls=self.worker_max_idle_polls,
            max_runs_per_invocation=self.worker_max_runs_per_invocation,
        )

    @property
    def agent_runtime(self) -> AgentRuntimeSettings:
        return AgentRuntimeSettings(
            llm_model=self.llm_model,
            recursion_limit=self.agent_recursion_limit,
            planner_mode=self.planner_mode,
        )
