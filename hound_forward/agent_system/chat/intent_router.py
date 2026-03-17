from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from hound_forward.agent_system.llm import OpenAIResponsesJSONClient
from hound_forward.domain import ChatContext, ChatIntent

logger = logging.getLogger(__name__)


class _IntentEnvelope(BaseModel):
    intent: ChatIntent


class IntentRouter:
    def __init__(self, model: str) -> None:
        self.model = model
        self.client = OpenAIResponsesJSONClient(model=model)

    def classify(self, *, message: str, context: ChatContext | None = None) -> ChatIntent:
        try:
            payload = self.client.create_json(
                system_prompt=self._system_prompt(),
                user_prompt=self._user_prompt(message=message, context=context),
                schema_name="intent_classification",
                schema=_IntentEnvelope.model_json_schema(),
            )
            intent = _IntentEnvelope.model_validate(payload).intent
            logger.info("Chat intent classified by LLM: %s", intent.value)
            return intent
        except Exception as exc:
            intent = self._fallback_intent(message=message, context=context)
            logger.warning("Intent classification fallback triggered: %s", exc)
            logger.info("Chat intent classified heuristically: %s", intent.value)
            return intent

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Classify the user's message for a research agent interface.\n"
            "Return JSON only.\n"
            "Use run_analysis for requests that should execute or re-run analysis.\n"
            "Use explain_result for requests about understanding an existing result.\n"
            "Use ask_question for conceptual or informational questions that do not require running the graph."
        )

    @staticmethod
    def _user_prompt(*, message: str, context: ChatContext | None) -> str:
        context_payload = context.model_dump(mode="json") if context is not None else {}
        return f"Message: {message}\nContext: {context_payload}"

    @staticmethod
    def _fallback_intent(*, message: str, context: ChatContext | None) -> ChatIntent:
        lowered = message.lower()
        explain_markers = ["what does this result mean", "explain this result", "what does this mean", "explain result"]
        run_markers = ["analyse", "analyze", "check", "run", "evaluate", "compute", "measure", "assess"]
        if context is not None and context.run_id and any(marker in lowered for marker in ("result", "mean", "explain", "why")):
            return ChatIntent.EXPLAIN_RESULT
        if any(marker in lowered for marker in explain_markers):
            return ChatIntent.EXPLAIN_RESULT
        if any(marker in lowered for marker in run_markers):
            return ChatIntent.RUN_ANALYSIS
        return ChatIntent.ASK_QUESTION
