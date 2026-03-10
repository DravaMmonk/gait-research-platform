from __future__ import annotations

import json

from hound_forward.ports import Job


class AzureServiceBusQueue:
    """Azure Service Bus adapter scaffold.

    The platform keeps Azure-specific transport concerns inside the adapter boundary.
    """

    def __init__(self, namespace: str, queue_name: str) -> None:
        self.namespace = namespace
        self.queue_name = queue_name
        self._buffer: list[str] = []

    def enqueue(self, job: Job) -> None:
        self._buffer.append(json.dumps({"run_id": job.run_id, "session_id": job.session_id, "payload": job.payload}))

    def dequeue(self) -> Job | None:
        if not self._buffer:
            return None
        payload = json.loads(self._buffer.pop(0))
        return Job(run_id=payload["run_id"], session_id=payload["session_id"], payload=payload["payload"])
