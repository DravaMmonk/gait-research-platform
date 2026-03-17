# PySR Architecture for Medical Research Agent

## Intent

This document defines how PySR should be introduced into the Hound Forward medical research agent architecture as the core symbolic search engine.

The objective is to make PySR a first-class research module while keeping it decoupled from orchestration, storage, review, and clinician workflow modules.

## Architectural Decision

PySR is the canonical symbolic regression engine for the medical research agent.

Within this architecture:

- the LLM agent is the research orchestrator
- PySR is the core formula search engine
- deterministic feature pipelines prepare search-ready inputs
- statistical validation ranks and filters PySR outputs
- clinician review remains the final scientific gate

PySR is therefore a core engine, but not a monolith. It must remain an isolated compute module with explicit input and output contracts.

## Why PySR

PySR is a strong fit for this platform because it already provides the core capabilities required for medical symbolic discovery:

- explicit symbolic expressions rather than black-box latent scores
- configurable operator sets
- complexity-aware search
- parallel evolutionary search
- structured equation outputs
- export into SymPy, LaTeX, JAX, and PyTorch formats
- warm-started continuation for iterative research workflows

It is particularly suitable when the platform needs to search a constrained formula space over curated, low-dimensional features rather than raw video or arbitrary embeddings.

## Architectural Position

The intended runtime shape is:

```text
research question
  -> agent planner
  -> variable-set proposal
  -> deterministic feature extraction
  -> search-ready tabular dataset
  -> PySR engine
  -> candidate equation frontier
  -> validation and ranking
  -> LLM interpretation
  -> clinician review
  -> controlled adoption
```

PySR owns the formula search stage only:

```text
search-ready dataset + search spec
  -> PySR fit
  -> ranked equations + evidence bundle
```

## Module Boundary

PySR must not be embedded directly inside agent logic, API handlers, or storage adapters.

The recommended boundary is:

- PySR runs as a compute module behind the `hound_forward.agent_tools` contract
- orchestration invokes it through a tool runner
- all persistence remains outside the PySR module

This preserves the current platform rule:

- local file input
- JSON and artifact output
- explicit config only
- no runtime coupling to queue, database, or blob adapters

## Decoupling Rules

The PySR module may:

- read a local feature table
- read a local search specification
- fit symbolic regression models
- emit equation artifacts and evaluation summaries

The PySR module may not:

- query Azure PostgreSQL directly
- write storage metadata records
- enqueue or manage runs
- call LLMs directly
- make review decisions
- infer product adoption status

This keeps PySR replaceable as a compute engine even if the rest of the platform evolves.

## Input Contract

PySR should consume a search package with a stable, explicit schema.

That schema should not be treated as a flat parameter blob. In this platform, the search manifest is a layered protocol document with separate medical, research, and compute concerns.

Minimum required inputs:

- feature table
- target definition
- feature metadata
- search specification
- split manifest
- provenance metadata

### 1. Feature table

The feature table is the direct search input. It should be a normalized tabular dataset in `parquet` or `csv` form.

Required properties:

- one row per training example
- one column per approved feature
- one target column or an external target vector
- stable feature names
- explicit missing-value policy applied before search

Expected examples:

- stride-derived metrics
- posture-derived metrics
- behavioral summary features
- physiological metadata
- environmental covariates

PySR should not be given raw video frames, raw pose sequences, or opaque embeddings as its primary input.

### 2. Target definition

The target definition should specify:

- target name
- task type
- label source
- label version
- cohort scope

Typical task types:

- regression
- binary classification expressed through an appropriate loss
- ranking-style or custom objective if justified

### 3. Feature metadata

The feature metadata should include:

- feature name
- human-readable description
- units
- approved source pipeline
- allowed transformations
- missingness notes

This metadata is required so downstream reviewers can interpret equations correctly.

### 4. Search specification

The search specification should include:

- allowed feature list
- `binary_operators`
- `unary_operators`
- complexity constraints
- nesting constraints
- loss definition
- selection policy
- runtime budget
- reproducibility settings

### Manifest design principle

The search manifest should be designed as a versioned protocol with three top-level sections:

- `medical_constraints`
- `research_definition`
- `search_config`

Supporting sections should include:

- `signals`
- `operator_registry`
- `formula_constraints`
- `validation`
- `experiment`

The detailed schema principles are documented in [pysr_manifest_schema_principles.md](/Users/drava/Documents/Hound/hf-playground/docs/pysr_manifest_schema_principles.md).

### 5. Split manifest

The split manifest should define:

- train, validation, and test membership
- cohort partitioning rules
- patient or dog-level leakage controls
- random seed and split version

### 6. Provenance metadata

Each search run should include:

- dataset version
- feature pipeline version
- search spec version
- reviewer or requestor identity
- execution timestamp

## Output Contract

The PySR module should emit an evidence bundle rather than a single best formula.

Minimum outputs:

- `equations.json`
- `equations.csv`
- `selected_equation.json`
- `metrics.json`
- `search_manifest.json`
- `provenance.json`
- optional exported expressions in SymPy and LaTeX
- optional serialized PySR state for continuation

### `equations.json`

This should contain the candidate frontier, including:

- equation string
- complexity
- loss
- score
- selection flag
- feature names used
- constant values

### `selected_equation.json`

This should contain:

- selected equation
- selection method
- target definition
- applicable feature requirements
- training and validation metrics
- warnings

### `metrics.json`

This should include:

- fit metrics
- held-out metrics
- cross-validation summary
- stability summary
- failure counts
- invalid-expression counts if available

### `search_manifest.json`

This should contain the exact PySR configuration used so the run is reproducible.

## Recommended Parameter Constraints

PySR is highly configurable. For this platform, the default posture should be conservative and medically interpretable rather than unconstrained.

Recommended baseline settings:

- use a small, clinically meaningful feature set
- use a constrained operator set
- use complexity penalties aggressively enough to suppress formula bloat
- preserve the full equation frontier for review
- prefer stable formulas over marginally better but more complex formulas

### Recommended default operator profile

Preferred baseline:

- `binary_operators=["+", "-", "*", "/"]`
- `unary_operators=["abs"]`

Allowed only when justified:

- `sqrt`
- `log1p`
- bounded custom ratio operators
- simple domain-safe transforms

Avoid by default:

- trigonometric operators
- exponential operators
- highly nested transformations
- unstable inverse-style operators without strong guardrails

### Recommended complexity controls

Recommended constraints:

- small `maxsize`
- shallow expression trees
- explicit `constraints`
- explicit `nested_constraints`
- moderate to strong complexity penalty

The design objective is not to search every possible equation. The objective is to search the clinically interpretable portion of the space.

### Recommended model selection

PySR supports `model_selection` values such as `accuracy`, `score`, and `best`.

For medical research workflows, `best` is the preferred default because it balances simplicity and fit more effectively than choosing the numerically most accurate expression by loss alone.

### Recommended reproducibility controls

When reproducibility is the priority:

- set `random_state`
- use `deterministic=True`
- use `parallelism="serial"`
- persist the full run manifest

This is slower than unconstrained parallel search, but appropriate for reviewable evidence generation.

For exploratory search, parallel settings may be used, but final candidate generation should be re-run in reproducible mode before review.

### Recommended search ergonomics

Useful options for this platform include:

- `select_k_features` when the approved variable set is still too large
- `denoise=True` only after explicit validation that denoising improves stability rather than masking signal problems
- `warm_start=True` for iterative research, but only when the search grammar remains unchanged

Warm starts should not be used casually across materially different operator sets or objectives.

## Integration Pattern

The clean integration pattern is:

```text
LLM planner
  -> search manifest
  -> staged run
  -> tool runner
  -> PySR module
  -> evidence bundle
  -> formula evaluation record
  -> interpretation and review
```

The LLM should never call PySR directly through ad hoc Python logic inside the graph. The graph should request a search run through the same structured execution path used by other compute modules.

## Suggested Internal Module Shape

The PySR engine should be introduced as a self-contained module with a narrow public interface.

Suggested shape:

```text
hound_forward/agent_tools/
  symbolic/
    pysr_engine.py
    io_models.py
    search_spec.py
    exporters.py
    cli.py
```

Suggested responsibilities:

- `pysr_engine.py`: owns fit and equation extraction
- `io_models.py`: typed request and response payloads
- `search_spec.py`: validates allowed search settings
- `exporters.py`: emits JSON, CSV, SymPy, and LaTeX outputs
- `cli.py`: exposes a file-based execution entry point

This keeps the engine accessible from local scripts, worker jobs, and future batch environments without linking it to a specific orchestration path.

## How Other Modules Should Depend on It

Other modules should depend on the PySR module through artifacts and typed manifests, not through internal Python object access.

Recommended dependency direction:

- agent layer depends on search manifests and search results
- worker runtime depends on the PySR CLI or typed entry point
- metadata services depend on persisted artifacts and summaries
- review tools depend on exported equations and metrics

No upstream module should assume PySR internals such as equation dataframe layout beyond the module's declared output schema.

## Statistical Validation Around PySR

PySR should be treated as the candidate generator, not the final arbiter of quality.

Validation wrapped around PySR should include:

- cross-validation
- held-out evaluation
- cohort stability checks
- missingness sensitivity
- noise sensitivity
- body-size and breed normalization review
- clinician plausibility review

The selected equation should be one that survives this process, not merely the top in-search candidate.

## Risks

Adopting PySR as the core search engine introduces real risks that must be managed deliberately.

### 1. Feature-table dependency

PySR is strongest on curated tabular inputs. If the upstream feature pipeline is weak, the search results will also be weak.

### 2. Spurious formula discovery

PySR can discover elegant but unstable formulas when datasets are small, biased, or noisy.

### 3. False interpretability

A short equation may look scientifically convincing while still reflecting leakage, confounding, or cohort bias.

### 4. Reproducibility tradeoffs

The fastest search settings are not always the most reproducible. Final review candidates must be rerun in reproducible mode.

### 5. Numerical fragility

Division-heavy or transform-heavy formulas can behave badly under real-world missingness, noise, and out-of-range values.

### 6. Search-space creep

If operator sets and nesting rules expand without discipline, the system will drift away from medical interpretability.

## Mitigations

The platform should mitigate these risks through:

- approved variable libraries
- search-spec validation
- constrained default operators
- reproducibility mode for final runs
- mandatory evidence bundles
- downstream robustness testing
- clinician review as a hard gate

## Rollout Plan

The recommended rollout is staged.

### Stage 1. Engine encapsulation

Introduce PySR as an isolated research module behind the `hound_forward.agent_tools` boundary.

### Stage 2. Manifest-driven search

Define a stable search manifest and artifact contract.

### Stage 3. Run integration

Expose PySR through formula evaluation runs rather than direct ad hoc invocation.

### Stage 4. Validation layer

Add cross-validation, cohort stability, and robustness summaries around raw PySR outputs.

### Stage 5. Review workflow

Connect evidence bundles to formula review and clinician review records.

### Stage 6. Controlled platform adoption

Promote only validated formulas into approved metric definitions.

## Decision Summary

PySR should be adopted as the core symbolic search engine for the Hound Forward medical research agent.

It is a strong fit because it already solves the central search problem well, exposes the right kinds of constraints, and produces interpretable formula outputs.

Its role, however, must remain precise:

- PySR is the core search engine
- the agent is the orchestrator
- validation is a separate layer
- review is a separate layer
- persistence is a separate layer

This separation keeps the platform scientifically governable and technically maintainable while allowing PySR to sit at the center of symbolic discovery.

## References

- PySR documentation: [https://ai.damtp.cam.ac.uk/pysr/dev/](https://ai.damtp.cam.ac.uk/pysr/dev/)
- PySR API reference: [https://ai.damtp.cam.ac.uk/pysr/v1.5.9/api.html](https://ai.damtp.cam.ac.uk/pysr/v1.5.9/api.html)
- PySR operators: [https://ai.damtp.cam.ac.uk/pysr/v1.5.9/operators](https://ai.damtp.cam.ac.uk/pysr/v1.5.9/operators)
- PySR backend customization: [https://ai.damtp.cam.ac.uk/pysr/v1.5.9/backend](https://ai.damtp.cam.ac.uk/pysr/v1.5.9/backend)
