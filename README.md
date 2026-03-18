# Hound Forward Research Platform

Hound Forward is now structured as a cloud-portable, AI-native research platform for canine movement analysis. The repository combines:

- a run-centric metadata layer backed by PostgreSQL semantics
- pluggable artifact storage backends
- queue-driven compute orchestration
- LangGraph-based agent orchestration through modular internal tools
- a research console scaffold for experiments, runs, metrics, datasets, and agent workflows

## Repository Layout

- `hound_forward/`: platform domain, application services, adapters, API, agent orchestration, modular tools, and deterministic local worker
- `hound_forward/manifests/`: versioned manifest examples for agent-planned protocol runs
- `db/schema.sql`: PostgreSQL schema for metadata
- `infra/azure/`: Bicep scaffold for Azure infrastructure
- `infra/gcp/`: Cloud Run deployment scripts for Google Cloud
- `frontend/research_console/`: Next.js research UI scaffold
- `frontend/research_console/components/ui/`: shared `shadcn/ui`-style primitive layer aligned to Hound Forward tokens
- `docs/`: platform architecture, agent architecture, deployment, and migration notes

## Core Model

The platform centers on these primary resources:

- `Session`
- `Run`
- `Asset`
- `MetricDefinition`
- `MetricResult`
- `ExperimentManifest`

All experiment, metric evaluation, and agent analysis activity is modeled as a run. The artifact store is backend-specific. Metadata remains PostgreSQL-only.

## Agent Tool Runtime

The current runtime slice is an agent-designed modular tool chain, not a production CV pipeline.

- `LangGraph planner`: selects the tool chain for a goal
- `Chat orchestrator`: routes chat requests into execution, explanation, or direct answers
- `Agent runtime`: consumes `agent-runs` jobs and coordinates LangGraph execution remotely
- `Run worker`: consumes `runs` jobs and executes modular stages such as video decode, keypoint extraction, metrics, and reporting
- `Job store`: persists `pending -> running -> completed/failed` state for remote agent jobs

The validated slice is:

```text
upload video
-> API enqueues agent job
-> agent runtime plans tool chain
-> agent creates run
-> agent enqueues run job
-> worker executes modular tools
-> tool-chain metrics output
-> agent stores result payload
```

The default tool chain writes:

- `keypoints.json`
- `metrics.json`
- `report.json`

## Formula Infrastructure

The repository includes infrastructure seams for formula-oriented evaluation without implementing formula business logic yet.

- `formula_definitions`, `formula_proposals`, `formula_evaluations`, and `formula_reviews` are scaffolded as metadata records
- formula-related runs are supported through dedicated `RunKind` values
- worker execution is driven by agent-designed staged execution plans

This stage prepares storage, execution, and review infrastructure. It does not implement formula DSL execution or clinician workflow logic yet.

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

Run the agent runtime:

```bash
python -m hound_forward.agent.main
```

Run the pipeline worker:

```bash
python -m hound_forward.worker.main
```

If you want to enable the real LLM-backed planner and chat orchestration on GCP, configure:

```bash
export HF_LLM_PROVIDER=vertex_ai
export HF_GCP_PROJECT_ID=...
export HF_GCP_LOCATION=australia-southeast2
export HF_LLM_MODEL=gemini-2.5-flash
export HF_PLANNER_MODE=hybrid
```

Start the research console scaffold:

```bash
cd frontend/research_console
npm install
npm run dev
```

Frontend architecture notes live in:

- [frontend/research_console/README.md](/Users/drava/Documents/Hound/hf-playground/frontend/research_console/README.md)

## Cloud Deployment Shape

The repository now supports two cloud deployment shapes:

- GCP with Cloud Run services, Pub/Sub push delivery, Cloud Storage, Cloud SQL, and Vertex AI Gemini
- Azure with Container Apps and Service Bus

The GCP path deploys:

- Artifact Registry for runtime images
- Cloud SQL for PostgreSQL for metadata
- Cloud Storage for videos, keypoints, signals, metrics, reports, and logs
- Pub/Sub topics and push subscriptions for `agent-runs` and `runs`
- Cloud Run for the API, agent runtime, and worker runtime
- Cloud Logging and Cloud Monitoring for observability

See:

- [docs/platform_architecture.md](/Users/drava/Documents/Hound/hf-playground/docs/platform_architecture.md)
- [docs/agent_architecture.md](/Users/drava/Documents/Hound/hf-playground/docs/agent_architecture.md)
- [docs/chat_orchestration.md](/Users/drava/Documents/Hound/hf-playground/docs/chat_orchestration.md)
- [docs/module_layout.md](/Users/drava/Documents/Hound/hf-playground/docs/module_layout.md)
- [docs/deployment_azure.md](/Users/drava/Documents/Hound/hf-playground/docs/deployment_azure.md)
- [docs/deployment_gcp.md](/Users/drava/Documents/Hound/hf-playground/docs/deployment_gcp.md)
- [docs/frontend_design_spec.md](/Users/drava/Documents/Hound/hf-playground/docs/frontend_design_spec.md)
- [docs/migration_from_mvp.md](/Users/drava/Documents/Hound/hf-playground/docs/migration_from_mvp.md)
- [docs/runtime_validation.md](/Users/drava/Documents/Hound/hf-playground/docs/runtime_validation.md)
- [docs/formula_infrastructure.md](/Users/drava/Documents/Hound/hf-playground/docs/formula_infrastructure.md)
- [docs/symbolic_regression_concepts.md](/Users/drava/Documents/Hound/hf-playground/docs/symbolic_regression_concepts.md)
- [docs/medical_symbolic_regression_principles.md](/Users/drava/Documents/Hound/hf-playground/docs/medical_symbolic_regression_principles.md)
- [docs/pysr_architecture.md](/Users/drava/Documents/Hound/hf-playground/docs/pysr_architecture.md)
- [docs/pysr_manifest_schema_principles.md](/Users/drava/Documents/Hound/hf-playground/docs/pysr_manifest_schema_principles.md)
- [docs/research_console_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/research_console_contract.md)

## Testing

Run the platform test suite:

```bash
pytest
```
