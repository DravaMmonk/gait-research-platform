# Worker Local Mode Contract

This document defines the long-lived contract for worker execution in local development.

The purpose of `local_mode` is not to create a separate worker implementation. The purpose is to preserve the same processing contract while removing cloud queue dependencies from the inner development loop.

## Core Principle

Local mode and cloud mode must execute the same worker logic.

The difference between them should be limited to how a job reaches the worker:

- local mode: direct invocation or local queue
- cloud mode: remote queue delivery such as Pub/Sub

The pipeline semantics, stage behavior, output artifacts, and run status transitions should remain aligned.

## Mode Contract

### Local Mode

Local mode is the development-facing execution path.

It should allow:

- direct processing of a run job without remote queue infrastructure
- use of in-memory or other local queue backends
- selective execution of pipeline stages
- use of mock or lightweight inference when appropriate

### Cloud Mode

Cloud mode is the integration-facing execution path.

It should allow:

- queue-driven processing from the deployed cloud transport
- real cloud storage integration
- real model execution when required
- end-to-end validation under deployed conditions

## Interface Invariants

Regardless of mode, the worker contract should preserve these invariants:

- the worker consumes the same logical job payload
- the worker writes the same classes of artifacts
- the worker drives the same run state machine
- the worker reports failures through the same error surface
- the worker supports the same pipeline stage boundaries

If local mode behaves differently from cloud mode in these areas, it stops being a valid development substitute.

## Required Execution Capabilities

The worker contract should support:

1. full pipeline execution
2. stage-by-stage execution
3. rerunning a downstream stage from previously materialized artifacts

At minimum, the stable conceptual stages are:

1. extract keypoints
2. compute metrics
3. generate report

Internal implementation can evolve, but these stage boundaries should remain addressable.

## Invocation Contract

The repository already exposes a stable local worker entrypoint:

```bash
python -m hound_forward.worker.main
```

The worker runtime also already exposes stable conceptual operations:

- process one job
- process a provided job directly
- process until idle

Current runtime implementation lives in:

- [hound_forward/worker/main.py](/Users/drava/Documents/Hound/hf-playground/hound_forward/worker/main.py)
- [hound_forward/worker/runtime.py](/Users/drava/Documents/Hound/hf-playground/hound_forward/worker/runtime.py)
- [hound_forward/worker/service.py](/Users/drava/Documents/Hound/hf-playground/hound_forward/worker/service.py)

Those files may evolve, but the execution model should remain equivalent.

## Local Queue Simulation Rules

A valid local mode may use:

- in-memory queueing
- direct method invocation
- a lightweight local queue backend

It should not require:

- Pub/Sub
- Cloud Run
- cloud-only IAM setup
- remote object storage

The local queue simulation should exist to remove infrastructure friction, not to redefine the worker contract.

## Mocking Rules

Local mode may replace expensive model execution with:

- dummy outputs
- fixture-based outputs
- lightweight local inference

However, mock execution must still preserve:

- output shape
- artifact naming expectations
- stage ordering
- failure behavior where practical

Mocking is acceptable. Contract drift is not.

## Configuration Rules

Local mode should remain compatible with the repository's local-first settings model:

- local metadata backend
- local artifact backend
- local or in-memory queue backend
- local worker runner

Current defaults are expressed in [`.env.example`](/Users/drava/Documents/Hound/hf-playground/.env.example).

The exact environment variable set may grow over time. The stable rule is that local mode must be activatable without cloud-only dependencies.

## What Must Stay Stable

To keep this document valid over time, the durable contract is:

- local mode is a transport change, not a pipeline rewrite
- local mode must support direct or local-queue execution
- local mode must preserve job semantics and artifact semantics
- pipeline stages must remain independently runnable
- local mode must not depend on Pub/Sub or Cloud Run

Specific helper functions, flags, and adapters may change without requiring this document to change.

## Related Documents

- [docs/local_cloudrun_dev_workflow.md](/Users/drava/Documents/Hound/hf-playground/docs/local_cloudrun_dev_workflow.md)
- [docs/dev_data_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/dev_data_contract.md)
- [docs/cloud_run_dev_deployment_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/cloud_run_dev_deployment_contract.md)
