from __future__ import annotations

from hound_forward.adapters.metadata import SqlAlchemyMetadataRepository
from hound_forward.adapters.queue import AzureServiceBusQueue, InMemoryJobQueue, PubSubJobQueue
from hound_forward.adapters.storage import AzureBlobArtifactStore, GCSArtifactStore
from hound_forward.adapters.storage.local import LocalArtifactStore
from hound_forward.agent_tools import AgentToolExecutor
from hound_forward.application import ResearchPlatformService, ServiceContainer
from hound_forward.pipeline import PlatformRunExecutor
from hound_forward.ports import ArtifactStore, JobQueue
from hound_forward.settings import PlatformSettings


def build_queue(*, settings: PlatformSettings, queue_name: str, topic: str, subscription: str | None = None) -> JobQueue:
    if settings.queue.backend == "azure_service_bus":
        if not settings.queue.azure_service_bus_namespace:
            raise ValueError("HF_AZURE_SERVICE_BUS_NAMESPACE is required when queue_backend=azure_service_bus.")
        return AzureServiceBusQueue(settings.queue.azure_service_bus_namespace, queue_name)
    if settings.queue.backend == "gcp_pubsub":
        if not settings.queue.gcp_project_id:
            raise ValueError("HF_GCP_PROJECT_ID is required when queue_backend=gcp_pubsub.")
        return PubSubJobQueue(
            project_id=settings.queue.gcp_project_id,
            topic=topic,
            subscription=subscription,
            endpoint=settings.queue.gcp_pubsub_endpoint,
        )
    return InMemoryJobQueue(queue_name=queue_name)


def build_artifact_store(settings: PlatformSettings) -> ArtifactStore:
    backend = settings.artifact_storage.backend
    if backend == "azure_blob":
        return AzureBlobArtifactStore(
            container=settings.artifact_storage.azure_blob_container,
            account_url=settings.artifact_storage.azure_blob_account_url,
            connection_string=settings.artifact_storage.azure_blob_connection_string,
        )
    if backend == "gcs":
        if not settings.artifact_storage.gcs_bucket:
            raise ValueError("HF_GCP_STORAGE_BUCKET is required when artifact_backend=gcs.")
        return GCSArtifactStore(
            bucket=settings.artifact_storage.gcs_bucket,
            project_id=settings.artifact_storage.gcp_project_id,
            endpoint=settings.artifact_storage.gcs_endpoint,
        )
    return LocalArtifactStore(settings.artifact_root_path())


def build_service(settings: PlatformSettings | None = None) -> ResearchPlatformService:
    resolved_settings = settings or PlatformSettings()
    metadata = SqlAlchemyMetadataRepository(resolved_settings.metadata_database_url)
    metadata.create_all()
    artifact_store = build_artifact_store(resolved_settings)
    tool_runner = AgentToolExecutor(
        artifact_store=artifact_store,
        work_root=resolved_settings.artifact_root_path() / "tool_runs",
    )
    executor = PlatformRunExecutor(metadata=metadata, tool_runner=tool_runner)
    return ResearchPlatformService(
        ServiceContainer(
            metadata=metadata,
            artifact_store=artifact_store,
            run_queue=build_queue(
                settings=resolved_settings,
                queue_name=resolved_settings.queue.run.name,
                topic=resolved_settings.queue.run.topic,
                subscription=resolved_settings.queue.run.subscription,
            ),
            agent_queue=build_queue(
                settings=resolved_settings,
                queue_name=resolved_settings.queue.agent.name,
                topic=resolved_settings.queue.agent.topic,
                subscription=resolved_settings.queue.agent.subscription,
            ),
            executor=executor,
            tool_runner=tool_runner,
        )
    )
