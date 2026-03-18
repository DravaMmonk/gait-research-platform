# GCP Infrastructure

This directory contains the operational assets for deploying the existing LangGraph runtime on Google Cloud without changing the agent architecture.

## Files

- `bootstrap.sh`: provisions the shared GCP resources and service accounts
- `deploy.sh`: builds, pushes, and deploys the three Cloud Run services
- `runtime.env.example`: documents the runtime contract used by the deploy script

## Runtime Topology

- one public Cloud Run service for the API
- one private Cloud Run service for the agent runtime
- one private Cloud Run service for the worker runtime
- Pub/Sub push subscriptions targeting the agent and worker services
- Cloud SQL for PostgreSQL
- Cloud Storage
- Artifact Registry

## Usage

1. Copy `runtime.env.example` to a local shell file and fill in the values.
2. Source that file into your shell.
3. Run `bash infra/gcp/bootstrap.sh`.
4. Run `bash infra/gcp/deploy.sh`.

The deploy script keeps the existing three-image topology and overrides the Cloud Run command only where an HTTP adapter is required.
