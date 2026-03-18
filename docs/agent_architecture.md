# Agent Architecture

## Intent

The agent layer is a research orchestrator, not a code authoring layer. It coordinates experiments, metric evaluation, and follow-up analysis through the platform tool boundary.

## Runtime Model

The production-aligned execution path is queue-driven:

```text
client request
  -> API
  -> jobs table (agent_execution, pending)
  -> queue transport for agent-runs
  -> agent runtime
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

The agent does not execute pipeline stages inline. It creates and observes `RunRecord` state while a separate worker consumes the `runs` queue or subscription.

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
- write directly to the metadata database
- push queue messages outside the application boundary
- manipulate object storage directly
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

In local validation mode, the graph may use an inline run monitor so the same contract can be exercised in one process. In cloud deployments, the graph only polls persisted run state.

## Cloud Run Path

The GCP deployment keeps the LangGraph runtime unchanged and adds small HTTP adapters around the existing agent and worker runtimes:

- Pub/Sub push sends job envelopes to Cloud Run
- `hound_forward.agent.service` decodes the agent job and calls `AgentRuntime.run_job`
- `hound_forward.worker.service` decodes the run job and calls `QueueWorkerRuntime.run_job`

This preserves the graph and application boundaries while making the runtime compatible with Cloud Run request handling.

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
