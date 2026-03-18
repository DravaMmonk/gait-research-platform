from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI

from hound_forward.adapters.queue.gcp_pubsub import PubSubJobQueue
from hound_forward.bootstrap import build_service
from hound_forward.settings import PlatformSettings
from hound_forward.worker.runtime import QueueWorkerRuntime


@lru_cache(maxsize=1)
def build_runtime() -> QueueWorkerRuntime:
    settings = PlatformSettings()
    service = build_service(settings)
    return QueueWorkerRuntime(service=service)


def create_app() -> FastAPI:
    app = FastAPI(title="Hound Forward Worker Runtime")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "hound-forward-worker"}

    @app.post("/pubsub/run-jobs")
    async def process_run_job(envelope: dict) -> dict:
        job = PubSubJobQueue.decode_push_envelope(envelope)
        run = build_runtime().run_job(job)
        return {"run_id": run.run_id, "status": run.status.value}

    return app


app = create_app()
