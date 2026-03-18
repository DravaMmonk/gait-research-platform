from __future__ import annotations

from collections import deque
from typing import ClassVar

from hound_forward.ports import Job


class InMemoryJobQueue:
    _queues: ClassVar[dict[str, deque[Job]]] = {}

    def __init__(self, queue_name: str = "default") -> None:
        self.queue_name = queue_name
        self._jobs = self._queues.setdefault(queue_name, deque())

    def enqueue(self, job: Job) -> None:
        self._jobs.append(job)

    def dequeue(self) -> Job | None:
        if not self._jobs:
            return None
        return self._jobs.popleft()
