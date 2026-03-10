# Platform Architecture

## Goal

Hound Forward is designed as a canine movement research platform rather than a standalone gait pipeline. The target shape is:

```text
Research Console
    -> Agent Orchestration (LangGraph)
    -> Tool Registry
    -> Research Platform Core
    -> Compute Pipeline
    -> Azure Storage / Queue / PostgreSQL
```

## Subsystems

### Research Platform Core

The platform core manages:

- sessions
- runs
- assets
- metric definitions
- metric results
- run events

### Compute Pipeline

The pipeline stays deterministic. It ingests manifests and produces structured outputs. Worker execution is queue-driven and artifact-backed.

### Agent Orchestration

LangGraph generates manifests, launches runs through tools, reads structured outcomes, and recommends next steps.

### Research Console

The Next.js scaffold reserves routes for:

- `/experiments`
- `/runs`
- `/metrics`
- `/datasets`
- `/agent-lab`

## Azure Mapping

- Azure PostgreSQL Flexible Server: metadata
- Azure Blob Storage: large artifacts
- Azure Service Bus: run queue
- Azure Container Apps: API and agent services
- Azure Container Apps Jobs / GPU VM: workers
- Azure Monitor: logs and run observability
