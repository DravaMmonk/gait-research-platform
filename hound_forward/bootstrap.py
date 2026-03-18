from __future__ import annotations

from hound_forward.adapters.metadata.azure_postgres import AzurePostgresMetadataRepository
from hound_forward.adapters.queue import AzureServiceBusQueue, InMemoryJobQueue
from hound_forward.adapters.storage.azure_blob import AzureBlobArtifactStore
from hound_forward.adapters.storage.local import LocalArtifactStore
from hound_forward.agent_tools import AgentToolExecutor
from hound_forward.application import ResearchPlatformService, ServiceContainer
from hound_forward.pipeline import PlatformRunExecutor
from hound_forward.ports import JobQueue
from hound_forward.settings import PlatformSettings


def build_queue(*, settings: PlatformSettings, queue_name: str) -> JobQueue:
    if settings.queue.backend == "azure_service_bus":
        if not settings.queue.azure_service_bus_namespace:
            raise ValueError("HF_AZURE_SERVICE_BUS_NAMESPACE is required when queue_backend=azure_service_bus.")
        return AzureServiceBusQueue(settings.queue.azure_service_bus_namespace, queue_name)
    return InMemoryJobQueue(queue_name=queue_name)


def build_service(settings: PlatformSettings | None = None) -> ResearchPlatformService:
    resolved_settings = settings or PlatformSettings()
    metadata = AzurePostgresMetadataRepository(resolved_settings.metadata_database_url)
    metadata.create_all()
    artifact_store = (
        AzureBlobArtifactStore(
            container=resolved_settings.azure_blob_container,
            account_url=resolved_settings.azure_blob_account_url,
            connection_string=resolved_settings.azure_blob_connection_string,
        )
        if resolved_settings.azure_blob_account_url or resolved_settings.azure_blob_connection_string
        else LocalArtifactStore(resolved_settings.artifact_root_path())
    )
    tool_runner = AgentToolExecutor(
        artifact_store=artifact_store,
        work_root=resolved_settings.artifact_root_path() / "tool_runs",
    )
    executor = PlatformRunExecutor(metadata=metadata, tool_runner=tool_runner)
    return ResearchPlatformService(
        ServiceContainer(
            metadata=metadata,
            artifact_store=artifact_store,
            run_queue=build_queue(settings=resolved_settings, queue_name=resolved_settings.queue.run_queue),
            agent_queue=build_queue(settings=resolved_settings, queue_name=resolved_settings.queue.agent_queue),
            executor=executor,
            tool_runner=tool_runner,
        )
    )
