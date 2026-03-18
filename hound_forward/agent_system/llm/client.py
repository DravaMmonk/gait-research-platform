from __future__ import annotations

from typing import Any

from hound_forward.settings import PlatformSettings

from .openai_responses import OpenAIResponsesJSONClient
from .vertex_ai import VertexAIResponsesJSONClient


class StructuredJSONClient:
    """Provider-backed JSON completion client for the agent layer."""

    def __init__(self, model: str, *, provider: str | None = None, settings: PlatformSettings | None = None) -> None:
        self.settings = settings or PlatformSettings()
        self.provider = (provider or self.settings.llm_provider).lower()
        self.model = model
        self._client = self._build_client()

    def create_json(self, *, system_prompt: str, user_prompt: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self._client.create_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_name=schema_name,
            schema=schema,
        )

    def _build_client(self) -> Any:
        if self.provider == "vertex_ai":
            return VertexAIResponsesJSONClient(model=self.model)
        if self.provider == "openai":
            return OpenAIResponsesJSONClient(model=self.model)
        raise ValueError(f"Unsupported HF_LLM_PROVIDER: {self.provider}")


def build_structured_json_client(
    *, model: str, provider: str | None = None, settings: PlatformSettings | None = None
) -> StructuredJSONClient:
    return StructuredJSONClient(model=model, provider=provider, settings=settings)
