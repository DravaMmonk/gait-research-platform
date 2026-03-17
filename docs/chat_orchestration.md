# Chat Orchestration

The research console chat surface is an agent interface, not a general-purpose chatbot. Every user message is routed through a backend chat orchestration layer that decides whether to:

- execute a new analysis through the constrained research graph
- explain an existing run result
- answer a direct question without executing the graph

## Core Flow

```text
Frontend chat
-> /api/chat
-> ChatOrchestrator
-> IntentRouter
-> Planner
-> ResearchGraph
-> Agent tools
-> ChatReasoner
-> Chat response
```

## Design Rules

- Chat does not bypass `planner -> graph -> tools` for analysis requests.
- The LLM is used for intent routing, constrained planning, and explanation.
- Execution remains bounded to the existing tool registry.
- Invalid or unsupported LLM plans fall back to the deterministic planner when planner mode is `hybrid`.
- The first implementation is text-first. Structured result payloads are still returned so the frontend can add richer module rendering later.

## Planner Modes

The backend supports three planner modes through `HF_PLANNER_MODE`:

- `hybrid`: use the LLM planner first, then fall back to the deterministic planner on invalid output or configuration gaps
- `llm`: prefer the LLM planner as the primary planner
- `deterministic`: disable the LLM planner entirely

The LLM model is configured through `HF_LLM_MODEL`. OpenAI access is provided through `OPENAI_API_KEY`.

## `/api/chat` Contract

Request:

```json
{
  "session_id": "session-123",
  "message": "Analyze my dog's gait",
  "context": {
    "run_id": "run-123",
    "asset_ids": ["asset-123"],
    "metric_name": "stride_length"
  }
}
```

Response:

```json
{
  "type": "run",
  "message": "The run completed successfully...",
  "run_id": "run-123",
  "progress_messages": [
    "Planning analysis...",
    "Running execution plan...",
    "Extracting keypoints...",
    "Computing metrics...",
    "Generating report...",
    "Explaining results...",
    "Done."
  ],
  "structured_data": {
    "manifest": {},
    "execution_plan": {},
    "run_summary": {},
    "metrics": [],
    "stage_results": [],
    "tool_trace": [],
    "evidence_context": {}
  }
}
```

The frontend uses `progress_messages` as pseudo-streaming text before rendering the final answer.

## Compatibility Notes

- `/agent/console/respond` remains available for compatibility with the older console contract.
- New chat development should target `/api/chat`.
- The CopilotKit adapter is a transport layer only. The backend orchestrator is the source of truth for chat behavior.
