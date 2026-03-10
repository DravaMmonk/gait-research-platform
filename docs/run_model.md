# Run Model

## Primary Resources

### Session

A session represents a research or intake context for one dog or one collection workflow.

### Run

A run is the canonical execution unit. Pipeline runs, metric evaluation, agent analysis, and experiment comparison all use the same top-level model.

### Asset

An asset is metadata that points to a Blob-backed artifact. The database stores the path, checksum, MIME type, and lightweight metadata only.

### MetricDefinition

A versioned metric contract with schema and description.

### MetricResult

A structured numeric output linked to both the run and the metric definition.

## Manifest

The `ExperimentManifest` drives execution. It contains:

- dataset selector
- pipeline specification
- metric list
- analysis list
- execution policy

The manifest is saved as a run asset and becomes part of the audit surface.
