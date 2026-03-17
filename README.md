# Hound Forward Research Platform

Hound Forward is now structured as an Azure-aligned, AI-native research platform for canine movement analysis. The repository combines:

- a run-centric metadata layer backed by Azure PostgreSQL semantics
- Azure Blob-aligned artifact storage
- queue-driven compute orchestration
- LangGraph-based agent orchestration through modular internal tools
- a research console scaffold for experiments, runs, metrics, datasets, and agent workflows

## Repository Layout

- `hound_forward/`: platform domain, application services, adapters, API, agent orchestration, modular tools, and deterministic local worker
- `hound_forward/manifests/`: versioned manifest examples for agent-planned protocol runs
- `db/schema.sql`: Azure PostgreSQL schema for metadata
- `infra/azure/`: Bicep scaffold for Azure infrastructure
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

All experiment, metric evaluation, and agent analysis activity is modeled as a run. Azure Blob stores large artifacts. Azure PostgreSQL stores metadata only.

## Agent Tool Runtime

The current runtime slice is an agent-designed modular tool chain, not a production CV pipeline.

- `LangGraph planner`: selects the tool chain for a goal
- `Chat orchestrator`: routes chat requests into execution, explanation, or direct answers
- `Agent tools`: execute modular stages such as video decode, keypoint extraction, metrics, and reporting
- `Local worker bridge`: drains queued runs so the same run contract can be exercised locally

The validated slice is:

```text
upload video
-> agent plans tool chain
-> create run
-> enqueue job
-> worker executes modular tools
-> tool-chain metrics output
-> agent reads result
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

If you want to enable the real LLM-backed planner and chat orchestration, configure:

```bash
export OPENAI_API_KEY=...
export HF_LLM_MODEL=gpt-4o-mini
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
- [docs/chat_orchestration.md](/Users/drava/Documents/Hound/hf-playground/docs/chat_orchestration.md)
- [docs/module_layout.md](/Users/drava/Documents/Hound/hf-playground/docs/module_layout.md)
- [docs/deployment_azure.md](/Users/drava/Documents/Hound/hf-playground/docs/deployment_azure.md)
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
