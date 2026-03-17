from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from hound_forward.agent_system.llm import OpenAIResponsesJSONClient

logger = logging.getLogger(__name__)


class _ReasonedText(BaseModel):
    message: str


class ChatReasoner:
    def __init__(self, model: str) -> None:
        self.model = model
        self.client = OpenAIResponsesJSONClient(model=model)

    def answer_question(self, *, message: str, session_summary: dict[str, Any]) -> str:
        fallback = f"Research agent answer: {message}"
        return self._complete_json(
            system_prompt=(
                "Answer the user's research question clearly and directly.\n"
                "You are a research agent assistant, not a casual chatbot.\n"
                "Return JSON only with a single 'message' field."
            ),
            user_prompt=f"Question: {message}\nSession summary: {session_summary}",
            fallback=fallback,
            schema_name="general_question_response",
        )

    def explain_result(self, *, message: str, result_payload: dict[str, Any]) -> str:
        fallback = (
            f"Result explanation for run {result_payload.get('run_id', 'unknown')}: "
            f"{result_payload.get('run_summary', {}).get('status', 'completed')}."
        )
        return self._complete_json(
            system_prompt=(
                "Explain the research run result using the provided structured outputs.\n"
                "Focus on what happened, what the metrics imply, and what to do next.\n"
                "Return JSON only with a single 'message' field."
            ),
            user_prompt=f"User message: {message}\nResult payload: {result_payload}",
            fallback=fallback,
            schema_name="result_explanation_response",
        )

    def _complete_json(self, *, system_prompt: str, user_prompt: str, fallback: str, schema_name: str) -> str:
        try:
            payload = self.client.create_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_name=schema_name,
                schema=_ReasonedText.model_json_schema(),
            )
            return _ReasonedText.model_validate(payload).message
        except Exception as exc:
            logger.warning("Reasoner fallback triggered: %s", exc)
            return fallback
