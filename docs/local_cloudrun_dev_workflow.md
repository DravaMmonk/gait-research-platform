# Local + Cloud Run Dev Workflow

This document defines the recommended development workflow for the current stage of the project. The goal is to keep the daily iteration loop fast while preserving a real cloud environment for correctness and performance validation.

## Core Decision

Use a dual-loop development model:

- local development for fast iteration
- a small Cloud Run `dev` environment for real pipeline validation

The cloud `dev` environment is important, but it must not sit on the critical path of day-to-day coding.

## Local Development

The default development loop should run locally:

- API: local process
- worker: local process
- frontend: Next.js dev server

This is the primary loop for:

- application logic
- API design
- UI work
- metric DSL and metric computation logic
- debugging worker behavior

Local development should optimize for seconds-level feedback, not production fidelity.

## Cloud Dev Environment

Maintain a separate Google Cloud `dev` environment using Cloud Run with intentionally small resources.

Recommended shape:

- Cloud Run `dev` API service
- Cloud Run `dev` worker service
- supporting GCP services such as Pub/Sub, Cloud Storage, and Vertex AI as needed by the real pipeline

Use this environment for:

- validating the real end-to-end pipeline
- running real videos
- measuring latency
- checking cloud integration correctness
- demo and pre-integration verification

This environment is a correctness and performance check, not the default daily development surface.

## CI/CD For Dev

The `dev` branch should automatically deploy to the cloud `dev` environment.

Recommended deployment flow:

```text
push to dev branch
-> Cloud Build
-> deploy to Cloud Run (dev)
```

This gives the team a continuously updated cloud environment without forcing local development to depend on remote deployment.

## The Key Productivity Rules

These rules create the largest development-speed gains.

### 1. Do Not Let AI Inference Block Daily Development

The main bottleneck is the runtime cost of video processing and model inference.

Split responsibilities:

- local: use mock inference, dummy results, or lightweight models
- cloud: use the real model stack on GCP

This produces a clean separation:

- `dev` local loop = fast feedback
- cloud `dev` loop = correctness check

Do not require full real inference to validate ordinary code changes.

### 2. Make The Pipeline Segmentable

The worker pipeline must support running individual stages independently.

At minimum, support:

1. extract keypoints
2. compute metrics
3. generate report

Avoid a design where every debugging session requires a full end-to-end rerun.

This should allow developers to rerun only the stage they are actively working on.

### 3. Make Intermediate Data Reusable

Create a reusable local development dataset, for example:

```text
/dev-data/
  video1.mp4
  keypoints.json
  metrics.json
```

This enables:

- skipping repeated inference runs
- faster debugging of downstream metric and reporting code
- deterministic comparisons across changes

For this project, reusable intermediate artifacts are a major force multiplier.

### 4. Support A Local Queue Simulation Mode

The worker must support both local direct execution and cloud queue-driven execution.

Example shape:

```python
if local_mode:
    process(video_path)
else:
    pull_from_pubsub()
```

This is critical. Many teams incorrectly force queue infrastructure into every local debug cycle and lose iteration speed.

The local mode should preserve the same processing contract while removing remote queue dependencies.

## Recommended Stack

### Local

- Python: FastAPI + `uv`
- queue: Redis or in-memory queue
- database: Supabase dev or local PostgreSQL
- storage: local filesystem

### Cloud On GCP

- Cloud Run for API and worker services
- Pub/Sub for queueing
- Cloud Storage for videos and artifacts
- Vertex AI for real model execution

### CI/CD

- Cloud Build for automatic deployment of the `dev` environment

## Dual-Loop Development Model

### Fast Loop: Local

```text
edit code -> run locally -> use mock data -> get feedback in seconds
```

Use this loop for:

- logic development
- UI development
- metric DSL work
- API design

### Slow Loop: Cloud

```text
push code -> auto deploy -> run real pipeline
```

Use this loop for:

- validation
- latency and performance testing
- demos

Both loops should exist at the same time. The local loop drives speed. The cloud loop protects correctness.

## Recommended Project Configuration

For the current project stage, the preferred setup is:

### Local

- API: local
- worker: local
- inference: mock or lightweight
- data: fixed reusable dataset

### Cloud

- Cloud Run: API + worker
- Pub/Sub: queue
- Vertex AI: real inference or GPU-backed model tasks

### CI/CD

- auto-deploy the `dev` environment
- keep it outside the normal inner development loop

## Summary

The project should not choose between local development and cloud development. It should use both, but for different jobs:

- local for speed
- Cloud Run `dev` for realism

That separation is what prevents video and inference costs from slowing down the entire team.

## Implementation Contracts

The stable supporting documents for this workflow are:

- [docs/local_run_commands.md](/Users/drava/Documents/Hound/hf-playground/docs/local_run_commands.md)
- [docs/dev_data_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/dev_data_contract.md)
- [docs/worker_local_mode_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/worker_local_mode_contract.md)
- [docs/cloud_run_dev_deployment_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/cloud_run_dev_deployment_contract.md)
