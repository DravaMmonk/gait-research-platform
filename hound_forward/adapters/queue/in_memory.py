from __future__ import annotations

from collections import deque

from hound_forward.ports import Job


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._jobs: deque[Job] = deque()

    def enqueue(self, job: Job) -> None:
        self._jobs.append(job)

    def dequeue(self) -> Job | None:
        if not self._jobs:
            return None
        return self._jobs.popleft()
