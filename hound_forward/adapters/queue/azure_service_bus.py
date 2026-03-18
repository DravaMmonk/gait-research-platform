from __future__ import annotations

import json
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusReceiveMode

from hound_forward.ports import Job, deserialize_job, serialize_job


def _normalize_namespace(namespace: str) -> str:
    return namespace if "." in namespace else f"{namespace}.servicebus.windows.net"


class AzureServiceBusQueue:
    """Service Bus queue adapter for queue-driven runtimes."""

    def __init__(self, namespace: str, queue_name: str) -> None:
        self.namespace = _normalize_namespace(namespace)
        self.queue_name = queue_name
        self._credential = DefaultAzureCredential()

    def enqueue(self, job: Job) -> None:
        payload = json.dumps(serialize_job(job))
        with ServiceBusClient(self.namespace, credential=self._credential) as client:
            with client.get_queue_sender(queue_name=self.queue_name) as sender:
                sender.send_messages(ServiceBusMessage(payload, content_type="application/json"))

    def dequeue(self) -> Job | None:
        with ServiceBusClient(self.namespace, credential=self._credential) as client:
            with client.get_queue_receiver(
                queue_name=self.queue_name,
                receive_mode=ServiceBusReceiveMode.RECEIVE_AND_DELETE,
                max_wait_time=1,
            ) as receiver:
                messages = receiver.receive_messages(max_message_count=1, max_wait_time=1)
                if not messages:
                    return None
                return self._deserialize(messages[0])

    @staticmethod
    def _deserialize(message: Any) -> Job:
        payload = json.loads(str(message))
        return deserialize_job(payload)
