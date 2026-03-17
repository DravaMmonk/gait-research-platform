# Module Layout

This repository is organized around a small number of product-facing boundaries.

## Root Principles

- keep executable platform code inside `hound_forward/`
- keep reference documents inside `docs/`
- keep deployment scaffolding inside `infra/`
- keep database schema inside `db/`
- keep the UI inside `frontend/research_console/`
- avoid top-level compatibility packages and one-off script folders when the same capability belongs in a package module

## Hound Forward Package

The Python package is split by responsibility:

- `hound_forward/agent_tools/`
  - modular, typed tools that the agent can compose into execution plans
  - each tool has a clear input kind and output kind
- `hound_forward/agent_system/`
  - LangGraph planning, orchestration, and tool-facing graph state
- `hound_forward/application/`
  - service boundary for sessions, runs, metrics, formulas, and console responses
- `hound_forward/domain/`
  - platform models and execution contracts
- `hound_forward/adapters/`
  - persistence, queue, storage, and infrastructure-facing adapters
- `hound_forward/pipeline/`
  - run execution over agent-designed stage plans
- `hound_forward/manifests/`
  - versioned example protocol manifests and future manifest utilities
- `hound_forward/tests/`
  - end-to-end tests for the supported runtime slice

## Agent Tools And Skills Mindset

The repo now follows the same modular shape that works well for tools and skills:

- each module should do one bounded job
- orchestration should depend on tool contracts, not implementation details
- example artifacts should live near the modules that understand them
- compatibility layers should be removed instead of kept as silent aliases
