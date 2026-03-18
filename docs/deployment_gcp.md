# GCP Deployment

This document describes the Google Cloud deployment path for the existing LangGraph-based runtime without changing the agent architecture.

## Design Goals

- keep the current `API -> agent queue -> agent runtime -> run queue -> worker` model
- keep the existing Dockerfiles and Python entrypoints
- run the API, agent runtime, and worker runtime on Cloud Run
- use Google-managed infrastructure for queueing, storage, metadata, and observability

## Deployment Shape

The GCP topology maps the current runtime to:

- Cloud Run service for the FastAPI API
- Cloud Run service for the agent runtime HTTP adapter
- Cloud Run service for the worker runtime HTTP adapter
- Pub/Sub topics and push subscriptions for `agent-runs` and `runs`
- Cloud SQL for PostgreSQL for metadata
- Cloud Storage for assets
- Artifact Registry for runtime images
- Cloud Build for image builds
- Cloud Logging and Cloud Monitoring for logs and metrics

## Why Push Subscriptions

The existing `hound_forward.agent.main` entrypoint is a long-running queue poller. That works well in local development and pull-based runtimes, but it is not a natural Cloud Run service entrypoint.

To preserve the LangGraph runtime while fitting Cloud Run:

- the API still enqueues jobs through the `JobQueue` abstraction
- Pub/Sub delivers those jobs to Cloud Run over authenticated HTTP push
- small FastAPI wrappers in `hound_forward/agent/service.py` and `hound_forward/worker/service.py` decode the Pub/Sub envelope and hand the job to the existing runtime logic

This keeps the core graph, tools, and run execution model unchanged while making the deployment Cloud Run-native.

## Runtime Contract

The GCP runtime expects these environment variables:

- `HF_ENVIRONMENT=gcp`
- `HF_METADATA_DATABASE_URL=postgresql+psycopg://...`
- `HF_ARTIFACT_BACKEND=gcs`
- `HF_GCP_PROJECT_ID=...`
- `HF_GCP_LOCATION=...`
- `HF_GCP_STORAGE_BUCKET=...`
- `HF_QUEUE_BACKEND=gcp_pubsub`
- `HF_GCP_PUBSUB_RUN_TOPIC=runs`
- `HF_GCP_PUBSUB_RUN_SUBSCRIPTION=runs-worker`
- `HF_GCP_PUBSUB_AGENT_TOPIC=agent-runs`
- `HF_GCP_PUBSUB_AGENT_SUBSCRIPTION=agent-runs-runtime`
- `HF_PLACEHOLDER_WORKER_MODE=false`
- `HF_LLM_PROVIDER=vertex_ai`
- `HF_LLM_MODEL=gemini-2.5-flash`

## Runtime Entry Points

The Cloud Run services use these Python entrypoints:

- API: `uvicorn hound_forward.api.app:app --host 0.0.0.0 --port 8080`
- agent runtime: `uvicorn hound_forward.agent.service:app --host 0.0.0.0 --port 8080`
- worker runtime: `uvicorn hound_forward.worker.service:app --host 0.0.0.0 --port 8080`

The original CLI entrypoints remain available for local development:

- `python -m hound_forward.agent.main`
- `python -m hound_forward.worker.main`

## Cloud SQL Connection Strategy

The deployment scripts use the Cloud SQL Unix socket path exposed by Cloud Run:

```text
/cloudsql/<project>:<region>:<instance>
```

That path is translated into `HF_METADATA_DATABASE_URL` for SQLAlchemy and Psycopg.

## Deployment Flow

1. Provision the base GCP resources with `infra/gcp/bootstrap.sh`.
2. Build and push the API, agent, and worker images with Cloud Build.
3. Deploy the three Cloud Run services with `infra/gcp/deploy.sh`.
4. Create or update Pub/Sub push subscriptions so they target the agent and worker service endpoints.
5. Apply `db/schema.sql` to the Cloud SQL database if schema creation is managed outside the app bootstrap.

## Build Strategy

The deployment script builds images with Cloud Build instead of local Docker. This avoids host architecture drift on Apple Silicon and guarantees Cloud Run-compatible manifests.

The repository now includes a `.gcloudignore` file so Cloud Build uploads only the runtime sources needed by the Dockerfiles.

## Bootstrap Responsibilities

`infra/gcp/bootstrap.sh` now prepares:

- Artifact Registry and the runtime storage bucket
- the Cloud Build source bucket
- IAM bindings for the default Compute Engine service account used by Cloud Build
- Cloud SQL, Pub/Sub topics, runtime service accounts, Vertex AI access, and Pub/Sub push impersonation

The Cloud Build service path requires:

- `roles/artifactregistry.writer`
- `roles/logging.logWriter`
- `roles/storage.objectAdmin` on the Cloud Build source bucket

The bootstrap script applies those bindings automatically.

## Files Introduced For GCP

- `hound_forward/adapters/queue/gcp_pubsub.py`
- `hound_forward/adapters/storage/gcs.py`
- `hound_forward/agent/service.py`
- `hound_forward/worker/service.py`
- `infra/gcp/bootstrap.sh`
- `infra/gcp/deploy.sh`
- `infra/gcp/runtime.env.example`

## Notes

- The frontend remains cloud-neutral and does not require GCP-specific code.
- Azure deployment assets remain available, but the runtime settings are now provider-neutral instead of Azure-first.
