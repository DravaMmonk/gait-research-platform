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

    def answer_question(
        self,
        *,
        message: str,
        session_summary: dict[str, Any],
        available_tools: list[dict[str, Any]] | None = None,
    ) -> str:
        fallback = f"Research agent answer: {message}"
        return self._complete_json(
            system_prompt=(
                "Answer the user's research question clearly and directly.\n"
                "You are a research agent assistant, not a casual chatbot.\n"
                "If the user asks about tools or capabilities, rely only on the provided available_tools list.\n"
                "Return JSON only with a single 'message' field."
            ),
            user_prompt=(
                f"Question: {message}\n"
                f"Session summary: {session_summary}\n"
                f"Available tools: {available_tools or []}"
            ),
            fallback=fallback,
            schema_name="general_question_response",
        )

    def describe_tools(
        self,
        *,
        message: str,
        session_summary: dict[str, Any],
        available_tools: list[dict[str, Any]],
    ) -> str:
        fallback = self._format_available_tools(available_tools)
        answer = self._complete_json(
            system_prompt=(
                "Answer questions about the agent's callable tools using only the provided available_tools list.\n"
                "Do not claim that you lack tool access when available_tools is not empty.\n"
                "Group tools by scope when helpful and mention what each tool is for.\n"
                "Return JSON only with a single 'message' field."
            ),
            user_prompt=(
                f"Question: {message}\n"
                f"Session summary: {session_summary}\n"
                f"Available tools: {available_tools}"
            ),
            fallback=fallback,
            schema_name="tool_inventory_response",
        )
        return answer if self._is_valid_tool_inventory_answer(answer, available_tools) else fallback

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

    @staticmethod
    def _format_available_tools(available_tools: list[dict[str, Any]]) -> str:
        if not available_tools:
            return "No callable tools are currently registered for this research agent."

        grouped_tools: dict[str, list[dict[str, Any]]] = {}
        for tool in available_tools:
            grouped_tools.setdefault(str(tool.get("scope", "unknown")), []).append(tool)

        sections: list[str] = ["I can call the following registered tools:"]
        for scope in sorted(grouped_tools):
            tools = sorted(grouped_tools[scope], key=lambda item: str(item.get("name", "")))
            label = "Graph execution tools" if scope == "graph_execution" else "Platform registry tools"
            sections.append(f"{label}:")
            for tool in tools:
                sections.append(
                    f"- {tool.get('name', 'unknown')}: {tool.get('description', 'No description available.')}"
                )
        return "\n".join(sections)

    @staticmethod
    def _is_valid_tool_inventory_answer(answer: str, available_tools: list[dict[str, Any]]) -> bool:
        normalized = answer.lower()
        if "do not have" in normalized or "don't have" in normalized or "no direct access" in normalized:
            return False
        tool_names = [str(tool.get("name", "")).lower() for tool in available_tools if tool.get("name")]
        return any(tool_name in normalized for tool_name in tool_names)
