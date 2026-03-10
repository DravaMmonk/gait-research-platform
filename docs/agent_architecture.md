# Agent Architecture

## Intent

The agent layer is a research orchestrator, not a code authoring layer. It coordinates experiments, metric evaluation, and follow-up analysis through the platform tool boundary.

## Runtime Model

The LangGraph research loop is:

```text
goal
  -> planner
  -> create_run
  -> enqueue_run
  -> monitor_run
  -> fetch_results
  -> analyze_results
  -> recommendation
```

## Boundaries

The agent may:

- generate an `ExperimentManifest`
- create runs
- enqueue runs
- fetch run status, assets, and metrics
- compare runs
- recommend the next experiment step

The agent may not:

- write source code
- write directly to Azure PostgreSQL
- push messages directly to Azure Service Bus
- manipulate Azure Blob Storage directly
- bypass the platform application layer

## Tool Surface

The primary tools are:

- `create_run`
- `get_run`
- `list_runs`
- `read_metrics`
- `compare_runs`
- `list_session_videos`
- `enqueue_run`

Each tool returns a structured `ToolResponse` payload so the graph never depends on free-text control flow.

In local runtime validation mode, the graph may wait through a `PlaceholderLocalWorkerBridge`. That bridge is explicitly a placeholder and not a production worker runtime.

## State Contract

The graph state stores:

- goal
- session id
- manifest
- run id
- run status
- run data
- metrics
- recommendation

All node inputs and outputs are typed. The graph performs reasoning only; execution always flows through tools.
