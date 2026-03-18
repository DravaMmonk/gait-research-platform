from __future__ import annotations

from hound_forward.bootstrap import build_service
from hound_forward.settings import PlatformSettings
from hound_forward.worker.runtime import QueueWorkerRuntime


def main() -> None:
    settings = PlatformSettings()
    service = build_service(settings)
    worker = QueueWorkerRuntime(service=service)
    processed = worker.run_until_idle(
        poll_interval_seconds=settings.worker_runtime.poll_interval_seconds,
        max_idle_polls=settings.worker_runtime.max_idle_polls,
        max_runs=settings.worker_runtime.max_runs_per_invocation,
    )
    print(f"Processed {processed} run job(s).")


if __name__ == "__main__":
    main()
