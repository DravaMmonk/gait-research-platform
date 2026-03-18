# Agent Architecture

## Intent

The agent layer is a research orchestrator, not a code authoring layer. It coordinates experiments, metric evaluation, and follow-up analysis through the platform tool boundary.

## Runtime Model

The production-aligned execution path is queue-driven:

```text
client request
  -> API
  -> jobs table (agent_execution, pending)
  -> Service Bus agent-runs queue
  -> agent container
  -> LangGraph research loop
  -> jobs table (completed or failed)
```

Inside the agent runtime, the LangGraph research loop remains:

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

The agent does not execute pipeline stages inline. It creates and observes `RunRecord` state while a separate worker consumes the `runs` queue.

## Boundaries

The agent may:

- generate an `ExperimentManifest`
- create runs
- enqueue runs through the application service
- fetch run status, assets, and metrics
- compare runs
- write structured job results and recommendations

The agent may not:

- write source code
- write directly to Azure PostgreSQL
- push queue messages outside the application boundary
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

In local validation mode, the graph may use an inline run monitor so the same contract can be exercised in one process. In Azure, the graph only polls persisted run state.

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

The remote job state is persisted separately:

- `job_id`
- `job_type`
- `status`
- `session_id`
- `run_id`
- `payload`
- `metadata`
- `result`
- `error`

All node inputs and outputs are typed. The graph performs reasoning only; execution always flows through tools and persisted state transitions.
