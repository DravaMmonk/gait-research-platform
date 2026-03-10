from __future__ import annotations

from hound_forward.api.app import build_service
from hound_forward.worker.runtime import PlaceholderLocalWorkerBridge


def main() -> None:
    service = build_service()
    worker = PlaceholderLocalWorkerBridge(service=service)
    result = worker.drain_once()
    if result is None:
        print("No queued jobs found.")
        return
    print(f"Processed run {result.run_id} with status {result.status.value}")


if __name__ == "__main__":
    main()
