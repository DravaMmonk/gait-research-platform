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

- `PlatformRunExecutor`: executes agent-designed modular tool stages
- `LocalArtifactStore`: placeholder local storage adapter
- `InMemoryQueue`: placeholder local queue
- `PlaceholderLocalWorkerBridge`: local worker boundary for agent and local testing

The pipeline ingests one uploaded video asset plus a manifest and produces structured fake outputs.

The next infrastructure layer adds a staged execution substrate:

- placeholder runtime validation stages
- research tool stages
- future formula evaluator stages

This keeps compute orchestration in one runtime model instead of spawning a separate formula execution system.

### Agent Orchestration

LangGraph generates manifests, launches runs through tools, reads structured outcomes, and recommends next steps.

### Research Console

The Next.js frontend currently exposes:

- `/`
  - the public CopilotKit-based agent console
- `/dev`
  - a hidden internal view library for visual modules and agent tool contracts

The public surface is intentionally chat-first and narrow. Preview content, module galleries, and tool contract references live in the hidden `/dev` route rather than the homepage.

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
