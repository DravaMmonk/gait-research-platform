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
- formula definitions
- formula proposals
- formula evaluations
- formula reviews

### Compute Pipeline

The current compute path is a runtime validation slice:

- `DummyRuntimeValidationPipeline`: deterministic fake computation
- `LocalArtifactStore`: placeholder local storage adapter
- `InMemoryQueue`: placeholder local queue
- `PlaceholderLocalWorkerBridge`: placeholder local worker boundary for agent and local testing

The pipeline ingests one uploaded video asset plus a manifest and produces structured fake outputs.

The next infrastructure layer adds a staged execution substrate:

- placeholder runtime validation stages
- research tool stages
- future formula evaluator stages

This keeps compute orchestration in one runtime model instead of spawning a separate formula execution system.

### Agent Orchestration

LangGraph generates manifests, launches runs through tools, reads structured outcomes, and recommends next steps.

### Research Console

The Next.js scaffold reserves routes for:

- `/experiments`
- `/runs`
- `/metrics`
- `/datasets`
- `/agent-lab`

The current UI is a placeholder Run Explorer focused on one uploaded video, one run, and one fake metric output set.

## Azure Mapping

- Azure PostgreSQL Flexible Server: metadata
- Azure Blob Storage: large artifacts
- Azure Service Bus: run queue
- Azure Container Apps: API and agent services
- Azure Container Apps Jobs / GPU VM: workers
- Azure Monitor: logs and run observability

## Formula Preparedness

The platform is now prepared to host:

- formula registry metadata
- formula proposal storage
- formula evaluation runs
- human review records

but it still does not claim formula business completeness.
