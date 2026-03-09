# GitHub Research Workflow

## Recommended Branch Model

Use a simple trunk-based workflow:

- `main`
- `feature/*`
- `experiment/*`
- `agent/*`

Examples:

- `feature/velocity-signal`
- `experiment/phase-representation`
- `agent/planner-updates`

## What belongs in pull requests

Pull requests should contain:

- platform code changes
- config templates
- docs
- tests

Pull requests should not contain:

- local result directories
- raw datasets
- cached intermediate artifacts

## How experiments are tracked

An experiment is defined by:

- a config file
- the Git revision used to run it
- the recorded runtime outputs

The runtime manifest should include at least:

- `experiment_id`
- `timestamp`
- `git_commit`
- `git_branch`
- `config_path`
- `status`
- summary metrics

## Role of GitHub Issues

Use Issues to track research questions, not only bugs.

Suggested labels:

- `research`
- `experiment`
- `representation`
- `signal`
- `agent`
- `bug`

Each issue should map to a hypothesis, capability gap, or evaluation question.

## Role of GitHub Projects

GitHub Projects should track the research program at a higher level:

- Backlog
- Signal Exploration
- Representation Learning
- Metric Discovery
- Clinical Validation

## CI boundaries

CI is for:

- unit tests
- config validation
- smoke experiments on toy data

CI is not for:

- long-running training
- expensive sweeps
- large dataset processing

## Release guidance

Use releases for capability milestones instead of experiment runs.

Examples:

- `v0.1.0` signal pipeline MVP
- `v0.2.0` contrastive representation baseline
- `v0.3.0` agent-assisted experimentation
