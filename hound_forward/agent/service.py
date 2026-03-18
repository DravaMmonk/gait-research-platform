from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI

from hound_forward.agent.runtime import AgentRuntime
from hound_forward.bootstrap import build_service
from hound_forward.settings import PlatformSettings


@lru_cache(maxsize=1)
def build_runtime() -> AgentRuntime:
    settings = PlatformSettings()
    service = build_service(settings)
    return AgentRuntime(service=service, settings=settings)


def create_app() -> FastAPI:
    app = FastAPI(title="Hound Forward Agent Runtime")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "hound-forward-agent"}

    @app.post("/pubsub/agent-jobs")
    async def process_agent_job(envelope: dict) -> dict:
        from hound_forward.adapters.queue import PubSubJobQueue

        if PubSubJobQueue is None:
            raise ModuleNotFoundError("google-cloud-pubsub is required to process Pub/Sub push envelopes.")
        job = PubSubJobQueue.decode_push_envelope(envelope)
        return build_runtime().run_job(job)

    return app


app = create_app()
