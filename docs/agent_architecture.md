# Agent Architecture

## Purpose

The agent layer is a research orchestration boundary, not a platform authoring tool. It is responsible for:

- generating experiment configs
- requesting approved execution
- reviewing structured results

It must not:

- modify source code
- perform Git operations
- preprocess datasets
- manipulate large raw data assets

## Core flow

The runtime flow is:

```text
goal
  -> agent.plan()
  -> candidate configs
  -> execution gate
  -> agent.run()
  -> structured result
  -> agent.review()
  -> next config recommendation
```

## Components

### `agents/llm_client.py`

Provides a single OpenAI-compatible transport abstraction:

- reads `OPENAI_API_KEY`
- reads `OPENAI_BASE_URL`
- reads `OPENAI_MODEL`
- exposes `generate(prompt, system_prompt=None)`

### `agents/experiment_planner.py`

Responsible for:

- prompt construction
- allowed-module enforcement
- recent experiment context assembly
- config normalization
- hard safety limits for MVP

Planner constraints:

- must use registered modules only
- must keep `epochs <= 50`
- must keep `embedding_dim <= 128`
- must return config-compatible JSON only

### `agents/experiment_agent.py`

Acts as the orchestrator:

- `plan()`
- `request_run()`
- `run()`
- `review()`

`request_run()` creates a deterministic approval handoff object. `run()` only executes when explicitly approved.

### `pipeline/run_experiment.py`

Owns:

- experiment directory creation
- stage tracking
- log creation
- manifest writing
- structured error capture

This is the only boundary that should catch runtime exceptions from experiments.

## Structured result contract

Every run returns a structured payload:

```json
{
  "experiment_id": "exp_001",
  "status": "success | failed",
  "result_dir": "path/to/results/exp_001",
  "metrics": {},
  "summary": {},
  "error": {
    "type": "ValueError",
    "message": "example",
    "traceback": null,
    "stage": "signal"
  }
}
```

## Stage model

Runtime stages are normalized to:

- `config`
- `signal`
- `training`
- `analysis`
- `persistence`

Failed runs must record the stage in both the returned result and `error.json`.

## Artifact model

Each result directory contains an auditable runtime record:

- `config.yaml`
- `logs.txt`
- `metrics.json`
- `summary.json`
- `error.json`
- `plots/`
- `artifacts/`

The global manifest at `results/manifest.jsonl` is the short index for the last N runs used by the planner and review layers.

## Review behavior

Review is LLM-first with a deterministic fallback.

### Success review

Inputs:

- metrics
- summary
- recent manifest context

Outputs:

- concise analysis
- next config-safe recommendation

### Failure review

Inputs:

- structured error
- summary
- recent manifest context

Outputs:

- failure explanation
- conservative next config change

Fallback rules are used when:

- no LLM client is configured
- the provider call fails
- the provider response is malformed
