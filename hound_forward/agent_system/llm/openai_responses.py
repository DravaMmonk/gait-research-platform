from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class OpenAIResponsesJSONClient:
    """Small wrapper around the OpenAI Responses API for strict JSON output."""

    def __init__(self, model: str) -> None:
        self.model = model
        self._client = self._build_client()

    @staticmethod
    def is_available() -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    def create_json(self, *, system_prompt: str, user_prompt: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("OpenAI Responses API is not configured.")
        response = self._client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise ValueError("Responses API returned no JSON payload.")
        return json.loads(output_text)

    @staticmethod
    def _build_client() -> Any:
        if not OpenAIResponsesJSONClient.is_available():
            return None
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - exercised indirectly in runtime setups
            logger.warning("OpenAI SDK is unavailable: %s", exc)
            return None
        return OpenAI()
