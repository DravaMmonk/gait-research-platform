from __future__ import annotations

import json
import logging
import os
from typing import Any

from hound_forward.settings import PlatformSettings

logger = logging.getLogger(__name__)


class OpenAIResponsesJSONClient:
    """Small wrapper around the OpenAI Responses API for strict JSON output."""

    def __init__(self, model: str) -> None:
        self.model = model
        self._client = self._build_client()

    @staticmethod
    def is_available() -> bool:
        return bool(os.getenv("OPENAI_API_KEY") or _read_openai_key_from_env_file(PlatformSettings()))

    def create_json(self, *, system_prompt: str, user_prompt: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("OpenAI Responses API is not configured.")
        normalized_schema = _normalize_openai_json_schema(schema)
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
                    "schema": normalized_schema,
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
        settings = PlatformSettings()
        api_key = os.getenv("OPENAI_API_KEY") or _read_openai_key_from_env_file(settings)
        if not api_key:
            return None
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - exercised indirectly in runtime setups
            logger.warning("OpenAI SDK is unavailable: %s", exc)
            return None
        return OpenAI(api_key=api_key)


def _read_openai_key_from_env_file(settings: PlatformSettings) -> str | None:
    env_file = settings.model_config.get("env_file")
    if not env_file:
        return None
    try:
        with open(env_file, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or not line.startswith("OPENAI_API_KEY="):
                    continue
                return line.split("=", 1)[1].strip()
    except OSError:
        return None
    return None


def _normalize_openai_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if isinstance(schema, dict):
        normalized = {key: _normalize_openai_json_schema(value) for key, value in schema.items()}
        if normalized.get("type") == "object":
            normalized.setdefault("additionalProperties", False)
            properties = normalized.get("properties")
            if isinstance(properties, dict):
                normalized["properties"] = {
                    key: _normalize_openai_json_schema(value) for key, value in properties.items()
                }
        if "$defs" in normalized and isinstance(normalized["$defs"], dict):
            normalized["$defs"] = {
                key: _normalize_openai_json_schema(value) for key, value in normalized["$defs"].items()
            }
        if "items" in normalized:
            normalized["items"] = _normalize_openai_json_schema(normalized["items"])
        if "anyOf" in normalized and isinstance(normalized["anyOf"], list):
            normalized["anyOf"] = [_normalize_openai_json_schema(item) for item in normalized["anyOf"]]
        return normalized
    if isinstance(schema, list):
        return [_normalize_openai_json_schema(item) for item in schema]
    return schema
