# Migration From MVP

## What Changed

The repository no longer treats `results/manifest.jsonl` or result directories as the platform source of truth.

The new source of truth is:

- Azure PostgreSQL-aligned metadata tables
- Blob-backed artifact records
- queue-driven run execution
- tool-driven agent orchestration

## What Was Preserved

The existing `gait_research_platform` package remains available as a legacy research algorithm surface. Signal builders, representation models, and experiment modules can be migrated incrementally into the new platform execution layer.

## What Was Retired

- local result-directory orchestration as the main runtime model
- agent-as-CLI-wrapper design
- documentation centered on a single-machine experiment MVP

## Next Migration Steps

- move legacy experiment execution behind the new run executor contract after runtime validation is complete
- replace local storage and queue adapters with Azure Blob and Service Bus bindings
- expand metric definitions into a richer DSL and clinician review workflow
- replace the dummy/fake/placeholder runtime validation pipeline with real CV-backed processing
