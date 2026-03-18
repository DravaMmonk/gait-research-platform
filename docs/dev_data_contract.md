# Dev Data Contract

This document defines the long-lived contract for reusable local development data.

Its purpose is to keep development fast, reproducible, and stage-addressable without forcing repeated inference runs.

## Goals

`dev-data/` exists to support:

- repeatable local debugging
- reuse of intermediate artifacts
- stage-by-stage pipeline execution
- deterministic comparisons across code changes

It is not a general-purpose raw data lake and it is not the production storage layout.

## Root Contract

The repository should treat `dev-data/` as the canonical local fixture root for development datasets.

Recommended top-level shape:

```text
dev-data/
  datasets/
    <dataset_id>/
      source/
      derived/
      manifests/
      notes/
```

This structure is intentionally generic so the project can grow without changing the contract.

## Dataset Contract

Each dataset should live under:

```text
dev-data/datasets/<dataset_id>/
```

`<dataset_id>` should be stable, human-readable, and safe for filenames.

Recommended examples:

- `golden-walk-001`
- `short-clinic-sample-a`
- `regression-turning-gait-01`

## Directory Responsibilities

### `source/`

Contains immutable input assets used to start pipeline runs.

Examples:

- `video.mp4`
- `video.mov`
- `metadata.json`

Rules:

- source files should be treated as read-only fixtures
- replacing a source file under the same dataset id is discouraged
- if the source changes materially, create a new dataset id

### `derived/`

Contains reusable outputs from intermediate and downstream pipeline stages.

Recommended shape:

```text
derived/
  keypoints/
  metrics/
  reports/
```

Examples:

- `derived/keypoints/default.json`
- `derived/metrics/default.json`
- `derived/reports/default.json`

Rules:

- derived artifacts must be reproducible from `source/`
- file naming should identify the profile or pipeline variant, not a temporary developer name
- derived artifacts may be regenerated, but regeneration should preserve the file contract

### `manifests/`

Contains run inputs, pipeline options, or execution descriptors that explain how the dataset was processed.

Examples:

- `pipeline.default.yaml`
- `pipeline.fast-local.yaml`
- `metrics.default.json`

Rules:

- manifests should describe how derived artifacts were produced
- manifests should be versionable and human-readable
- a dataset should be understandable without external chat history

### `notes/`

Contains lightweight documentation for humans.

Examples:

- `README.md`
- `known_issues.md`
- `expected_observations.md`

Rules:

- notes should capture why the dataset exists
- notes should describe any intentional quirks or expected outputs

## Minimum Useful Dataset

A dataset is considered development-ready when it includes:

- at least one source video
- enough metadata to identify what the sample is
- either a manifest or a short dataset note

A dataset becomes high-value when it also includes:

- reusable `keypoints.json`
- reusable `metrics.json`
- a reference report artifact

## Artifact Naming Rules

Use semantic names that survive implementation churn.

Preferred naming:

- `default.json`
- `fast-local.json`
- `vertex-baseline.json`
- `report.default.json`

Avoid naming based on:

- temporary branches
- developer initials
- dates that do not carry semantic meaning

The key idea is that filenames should describe the processing profile, not the moment they were created.

## Provenance Rules

Every reusable derived artifact should be attributable to:

- a source dataset id
- a processing profile
- a pipeline or manifest definition

This provenance can be stored either:

- in a sidecar metadata file
- inside the artifact payload
- in a manifest within `manifests/`

The mechanism can evolve. The requirement for provenance should not.

## What Must Stay Stable

To keep this document valid over time, the durable contract is:

- `dev-data/` is the local reusable fixture root
- datasets are grouped by stable dataset ids
- source and derived assets are kept separate
- keypoints, metrics, and reports are first-class reusable intermediate artifacts
- every reusable derived artifact must be traceable to an input and a processing profile

Exact file formats, schema versions, and helper scripts may change without invalidating this document.

## Related Documents

- [docs/local_cloudrun_dev_workflow.md](/Users/drava/Documents/Hound/hf-playground/docs/local_cloudrun_dev_workflow.md)
- [docs/local_run_commands.md](/Users/drava/Documents/Hound/hf-playground/docs/local_run_commands.md)
- [docs/worker_local_mode_contract.md](/Users/drava/Documents/Hound/hf-playground/docs/worker_local_mode_contract.md)
