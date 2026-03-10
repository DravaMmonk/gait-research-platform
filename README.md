# Hound Forward Research Platform

Hound Forward is now structured as an Azure-aligned, AI-native research platform for canine movement analysis. The repository combines:

- a run-centric metadata layer backed by Azure PostgreSQL semantics
- Azure Blob-aligned artifact storage
- queue-driven compute orchestration
- LangGraph-based agent orchestration through typed tools
- a research console scaffold for experiments, runs, metrics, datasets, and agent workflows

## Repository Layout

- `hound_forward/`: platform domain, application services, adapters, API, agent orchestration, and deterministic local worker
- `gait_research_platform/`: reusable legacy research algorithms kept as a compatibility surface while the platform migrates
- `db/schema.sql`: Azure PostgreSQL schema for metadata
- `infra/azure/`: Bicep scaffold for Azure infrastructure
- `frontend/research_console/`: Next.js research UI scaffold
- `docs/`: platform architecture, agent architecture, deployment, and migration notes

## Core Model

The platform centers on these primary resources:

- `Session`
- `Run`
- `Asset`
- `MetricDefinition`
- `MetricResult`
- `ExperimentManifest`

All experiment, metric evaluation, and agent analysis activity is modeled as a run. Azure Blob stores large artifacts. Azure PostgreSQL stores metadata only.

## Local Development

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Use the local settings scaffold:

```bash
cp .env.example .env
```

Run the FastAPI service:

```bash
uvicorn hound_forward.api.app:app --reload
```

Start the research console scaffold:

```bash
cd frontend/research_console
npm install
npm run dev
```

## Azure Deployment Shape

The target Azure deployment includes:

- Azure PostgreSQL Flexible Server for metadata
- Azure Blob Storage for videos, keypoints, signals, metrics, reports, and logs
- Azure Service Bus for queued runs
- Azure Container Apps for the API and agent runtime
- Azure Container Apps Jobs for workers
- Azure Monitor and Log Analytics for observability

See:

- [docs/platform_architecture.md](/Users/drava/Documents/Hound/hf-playground/docs/platform_architecture.md)
- [docs/agent_architecture.md](/Users/drava/Documents/Hound/hf-playground/docs/agent_architecture.md)
- [docs/deployment_azure.md](/Users/drava/Documents/Hound/hf-playground/docs/deployment_azure.md)
- [docs/migration_from_mvp.md](/Users/drava/Documents/Hound/hf-playground/docs/migration_from_mvp.md)

## Testing

Run the platform test suite:

```bash
pytest
```
