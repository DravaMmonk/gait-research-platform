# Research Console Contract

## Intent

This document defines the first stable backend/frontend contract for the agent-first research console.

The contract is designed so the backend can select controlled visual modules and the frontend can render them without free-form UI generation.

## Endpoint

`POST /agent/console/respond`

## Request

```json
{
  "session_id": "session-console-001",
  "message": "Compare this dog's mobility over the last 6 months and show as table only.",
  "display_preferences": ["table_only"],
  "active_context": {
    "run_id": "run-001",
    "metric_name": "mobility_index_v2"
  }
}
```

### Request fields

- `session_id`: required session scope
- `message`: user natural-language prompt
- `display_preferences`: optional structured display overrides
- `active_context`: optional selected session, run, metric, formula, or asset context

## Response

```json
{
  "thread": [],
  "message": "The console assembled a summary and evidence-aware table response.",
  "modules": [],
  "view_modes": ["table", "evidence"],
  "tool_trace": [],
  "evidence_context": {
    "metric_definition": "mobility_index_v2",
    "time_range": "Last 6 months",
    "data_quality": "2 sessions contain incomplete metadata.",
    "clinician_reviewed": true,
    "derived_metric": true,
    "references": ["run-001", "formula:mobility_index_v2"]
  },
  "warnings": [],
  "suggested_followups": []
}
```

## Response fields

- `thread`: user and assistant conversation items
- `message`: plain-language assistant summary
- `modules`: controlled visual module payloads
- `view_modes`: available frontend view mode tabs
- `tool_trace`: execution and selection trace for operator visibility
- `evidence_context`: shared evidence metadata for the inspector rail
- `warnings`: non-fatal issues or important caveats
- `suggested_followups`: quick next-step prompts

## Supported display preferences

- `table_only`
- `prefer_chart`
- `prefer_video`
- `raw_values_only`
- `evidence_first`

## Supported view modes

- `summary`
- `chart`
- `table`
- `evidence`
- `video`
- `formula`

## Module registry

### `summary_card`

Purpose:
- concise conclusion
- key status
- highlight metadata

### `trend_chart`

Purpose:
- time-based metric visualization
- trend and anomaly review

### `metric_table`

Purpose:
- raw or derived numeric inspection
- sort-friendly evidence view

### `evidence_panel`

Purpose:
- provenance
- confidence
- missingness
- review status

### `formula_explanation_card`

Purpose:
- formula display
- interpretation
- assumptions

### `video_panel`

Purpose:
- session evidence anchor
- timestamp-scoped review surface

### `comparison_cards`

Purpose:
- compact side-by-side deltas
- month-over-month or cohort comparison

## Contract rules

- The backend may select and order modules.
- The frontend may filter modules by view mode.
- The frontend may not reinterpret module payloads into new semantic types.
- The backend may not return arbitrary HTML or frontend code.
- Evidence context is required for every successful analytical response.

## First implementation behavior

The first implementation is placeholder-aware:

- it uses deterministic scaffold data where live orchestration is not yet available
- it keeps production-shaped request and response models
- it preserves the platform principle that agents select from a controlled schema rather than generating arbitrary interfaces
