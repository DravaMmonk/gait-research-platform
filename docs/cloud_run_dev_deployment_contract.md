# Cloud Run Dev Deployment Contract

This document defines the long-lived deployment contract for the Google Cloud `dev` environment.

It is not intended to duplicate one-off operational steps. It records the durable conventions that should remain true even if CI configuration, build internals, or resource sizes change.

## Purpose

The Cloud Run `dev` environment exists to provide:

- real end-to-end pipeline validation
- real cloud integration checks
- real video processing runs
- latency and performance measurements
- demo and verification environments

It does not exist to replace the local inner development loop.

## Deployment Trigger Contract

The `dev` environment should be automatically updated from the `dev` branch.

The durable deployment flow is:

```text
push to dev branch
-> Cloud Build
-> deploy to Cloud Run (dev)
```

The exact CI system wiring may evolve. The branch-to-build-to-deploy contract should remain stable.

## Topology Contract

For this repository, the current orchestration model is a three-service runtime:

- API service
- agent runtime service
- worker runtime service

The `dev` deployment should preserve that runtime shape unless the platform architecture itself changes.

On GCP, the `dev` environment should continue to use:

- Cloud Run for deployed runtime services
- Pub/Sub for queue delivery
- Cloud Storage for artifact and media storage
- Cloud SQL for metadata
- Vertex AI for real model-backed execution when needed

## Environment Separation Rules

The `dev` environment must remain isolated from production.

It should use:

- dedicated service names
- dedicated storage
- dedicated database resources
- dedicated queue resources
- dedicated service accounts where practical

The point of `dev` is realistic validation without production coupling.

## Resource Sizing Rules

The `dev` environment should use small or moderate resources by default.

The goal is:

- enough capacity to validate correctness
- enough capacity to run real samples
- enough capacity to observe latency
- not enough capacity to turn `dev` into an always-on production clone

Exact CPU, memory, concurrency, and scaling values are implementation details and may change without changing this document.

## Runtime Contract

The deployed Cloud Run services should continue to be configured by environment variables that define:

- environment identity
- metadata backend
- artifact backend
- queue backend
- queue topic and subscription names
- model provider and model selection

Current examples live in:

- [infra/gcp/runtime.env.example](/Users/drava/Documents/Hound/hf-playground/infra/gcp/runtime.env.example)
- [docs/deployment_gcp.md](/Users/drava/Documents/Hound/hf-playground/docs/deployment_gcp.md)

The specific variable list can evolve. The durable rule is that `dev` deployment remains configuration-driven and environment-specific.

## Service Exposure Rules

The API service may be public when needed for development workflows.

Agent and worker runtimes should be private by default unless architecture changes require otherwise.

Push-driven queue delivery should remain authenticated.

## Deployment Ownership Rules

The source of truth for infrastructure implementation should remain in repository-managed assets.

Current implementation assets are:

- [infra/gcp/bootstrap.sh](/Users/drava/Documents/Hound/hf-playground/infra/gcp/bootstrap.sh)
- [infra/gcp/deploy.sh](/Users/drava/Documents/Hound/hf-playground/infra/gcp/deploy.sh)
- [infra/gcp/runtime.env.example](/Users/drava/Documents/Hound/hf-playground/infra/gcp/runtime.env.example)

These scripts may change. The durable contract is that the repository owns and documents the `dev` deployment path.

## What Dev Must Validate

The Cloud Run `dev` environment should remain the place to validate:

- real queue delivery
- real storage integration
- real artifact generation
- real cloud runtime behavior
- latency against realistic workloads

It should not become the required surface for:

- ordinary API iteration
- ordinary worker debugging
- every frontend change

## What Must Stay Stable

To keep this document valid over time, the durable contract is:

- `dev` deploys automatically from the `dev` branch
- Cloud Build performs the build step
- Cloud Run hosts the deployed `dev` services
- the cloud `dev` environment is separate from the local inner loop
- the cloud `dev` environment is realistic but intentionally small
- deployment remains repository-defined and configuration-driven

Detailed CI syntax, script flags, and resource sizes may change without invalidating this document.

## Related Documents

- [docs/local_cloudrun_dev_workflow.md](/Users/drava/Documents/Hound/hf-playground/docs/local_cloudrun_dev_workflow.md)
- [docs/deployment_gcp.md](/Users/drava/Documents/Hound/hf-playground/docs/deployment_gcp.md)
- [docs/worker_local_mode_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/worker_local_mode_contract.md)
