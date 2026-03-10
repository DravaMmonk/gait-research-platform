# Engineering Principles

## Project Type

This repository is a hybrid of:

- platform engineering
- movement science research
- metric discovery
- agent-assisted experimentation

The platform boundary should stay stable while manifests, metrics, and cohorts evolve quickly.

## Core Principles

### 1. Everything is a run

Pipeline execution, metric evaluation, experiment comparison, and agent analysis are all modeled as runs.

### 2. Metadata belongs in Azure PostgreSQL

- sessions, runs, assets, metrics, and run events are metadata
- the database is the source of truth for orchestration state
- large artifacts do not belong in the database

### 3. Artifacts belong in storage

- videos, keypoints, signals, metric exports, plots, reports, and logs belong in Blob-backed storage
- the database stores paths, checksums, and lightweight metadata only

### 4. Agents reason, tools execute

- agents generate manifests and recommendations
- tools perform side effects
- agents do not reach into the filesystem, queue, or database directly

### 5. Deterministic compute, structured outputs

- pipeline steps stay deterministic
- outputs are structured JSON and registered assets
- free-text is not a control plane

### 6. Local parity with Azure

- local development uses the same domain model and schema shape
- moving to Azure changes adapters and environment wiring, not the application model
