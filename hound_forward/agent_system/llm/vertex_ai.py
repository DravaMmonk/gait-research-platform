from __future__ import annotations

import json
import logging
import os
from typing import Any

from hound_forward.settings import PlatformSettings

logger = logging.getLogger(__name__)


class VertexAIResponsesJSONClient:
    """Wrapper around Vertex AI Gemini for JSON-schema-constrained responses."""

    def __init__(self, model: str, *, project_id: str | None = None, location: str | None = None) -> None:
        self.model = model
        self.project_id = project_id or _resolve_gcp_project_id(PlatformSettings())
        self.location = location or _resolve_gcp_location(PlatformSettings())
        self._client = self._build_client()

    @staticmethod
    def is_available() -> bool:
        settings = PlatformSettings()
        if not _resolve_gcp_project_id(settings):
            return False
        try:
            from google import genai  # noqa: F401
        except ImportError:
            return False
        return True

    def create_json(self, *, system_prompt: str, user_prompt: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("Vertex AI Gemini is not configured.")

        response = self._generate_with_schema(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
        )
        output_text = _extract_response_text(response)
        if not output_text:
            raise ValueError(f"Vertex AI Gemini returned no JSON payload for {schema_name}.")
        return json.loads(output_text)

    def _generate_with_schema(self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> Any:
        from google.genai import types

        try:
            return self._client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
        except Exception as exc:
            logger.warning("Vertex AI schema-constrained generation failed; retrying with prompt-only schema guidance: %s", exc)
            return self._client.models.generate_content(
                model=self.model,
                contents=(
                    f"{user_prompt}\n\n"
                    "Return JSON only that matches this JSON Schema:\n"
                    f"{json.dumps(schema, separators=(',', ':'))}"
                ),
                config=types.GenerateContentConfig(
                    temperature=0,
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )

    def _build_client(self) -> Any:
        if not self.project_id:
            return None
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - exercised indirectly in runtime setups
            logger.warning("google-genai SDK is unavailable: %s", exc)
            return None
        return genai.Client(vertexai=True, project=self.project_id, location=self.location)


def _resolve_gcp_project_id(settings: PlatformSettings) -> str | None:
    return (
        settings.gcp_project_id
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
    )


def _resolve_gcp_location(settings: PlatformSettings) -> str:
    return (
        os.getenv("HF_GCP_LOCATION")
        or os.getenv("GOOGLE_CLOUD_LOCATION")
        or os.getenv("GOOGLE_CLOUD_REGION")
        or os.getenv("GCP_REGION")
        or settings.gcp_location
        or "global"
    )


def _extract_response_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return text

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        fragments = [getattr(part, "text", "") for part in parts if getattr(part, "text", None)]
        if fragments:
            return "".join(fragments)
    return ""
