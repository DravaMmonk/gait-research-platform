from __future__ import annotations

import json
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusReceiveMode

from hound_forward.ports import Job


def _normalize_namespace(namespace: str) -> str:
    return namespace if "." in namespace else f"{namespace}.servicebus.windows.net"


class AzureServiceBusQueue:
    """Service Bus queue adapter for queue-driven runtimes."""

    def __init__(self, namespace: str, queue_name: str) -> None:
        self.namespace = _normalize_namespace(namespace)
        self.queue_name = queue_name
        self._credential = DefaultAzureCredential()

    def enqueue(self, job: Job) -> None:
        payload = self._serialize(job)
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
    def _serialize(job: Job) -> str:
        return json.dumps(
            {
                "job_id": job.job_id,
                "job_type": job.job_type,
                "run_id": job.run_id,
                "session_id": job.session_id,
                "payload": job.payload,
                "metadata": job.metadata,
            }
        )

    @staticmethod
    def _deserialize(message: Any) -> Job:
        payload = json.loads(str(message))
        return Job(
            job_id=payload["job_id"],
            job_type=payload["job_type"],
            run_id=payload["run_id"],
            session_id=payload.get("session_id"),
            payload=payload.get("payload", {}),
            metadata=payload.get("metadata", {}),
        )
