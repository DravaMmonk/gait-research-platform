from __future__ import annotations

import json
import os
from typing import Any


class LLMClient:
    def generate(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2) -> str:
        raise NotImplementedError


class OpenAICompatibleClient(LLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.default_model = default_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed. Install the 'agent' extra.") from exc

        client_kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = OpenAI(**client_kwargs)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=self.default_model,
            temperature=temperature,
            messages=messages,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("LLM returned an empty response.")
        return content


def config_from_llm_output(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(lines[1:-1]).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM output could not be parsed as JSON config.") from exc
