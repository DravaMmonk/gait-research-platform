# Engineering Principles

## Project Type

This repository is a hybrid of:

- platform engineering
- representation learning research
- configuration-driven experimentation

The codebase is intentionally organized so the platform remains stable while experiments change rapidly.

## Core Principles

### 1. Platform and experiments are separate concerns

- platform code lives in Python modules under `gait_research_platform/`
- experiments are defined primarily through YAML configs
- experiment outputs are runtime artifacts, not source-controlled assets

### 2. Agent actions must remain auditable

- agents generate configs
- agents run experiments
- agents read results and recommend next steps
- agents do not modify source code, commit, or push changes

### 3. Reproducibility is a first-class feature

Every experiment should be reconstructable from:

- code revision
- config
- runtime manifest
- saved artifacts

`manifest.jsonl` and per-run `summary.json` are the canonical runtime records.

### 4. Extension points should be explicit

New components enter through registries:

- signals
- representations
- experiments
- analysis tasks
- pose extractors

This keeps the research surface expandable without turning the runtime into ad-hoc import logic.

### 5. Local results, versioned configs

- code and configs belong in Git
- large data and experiment results do not
- generated configs may be committed when they represent durable research decisions

## Repository Boundaries

Keep in Git:

- platform code
- YAML configs
- docs
- tests
- lightweight sample utilities

Keep out of Git:

- raw videos
- pose parquet dumps
- cached signals
- learned embeddings
- result directories
- local virtualenvs and caches
