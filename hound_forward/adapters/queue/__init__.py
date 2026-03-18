from __future__ import annotations

from .in_memory import InMemoryJobQueue

try:
    from .azure_service_bus import AzureServiceBusQueue
except ModuleNotFoundError:  # optional dependency
    AzureServiceBusQueue = None

try:
    from .gcp_pubsub import PubSubJobQueue
except ModuleNotFoundError:  # optional dependency
    PubSubJobQueue = None

__all__ = ["AzureServiceBusQueue", "PubSubJobQueue", "InMemoryJobQueue"]
