# PySR Search Manifest Schema Principles

## Intent

This document defines the schema design principles for the PySR search manifest used by the Hound Forward medical research agent.

The design objective is to preserve medical meaning while retaining enough search flexibility to support new discoveries. The manifest is therefore treated as a versioned research protocol, not just a bag of algorithm parameters.

## Core Requirement

In a medical symbolic regression workflow, the manifest must do two things at the same time:

- constrain the search space so outputs remain clinically interpretable
- preserve enough expressive freedom for valid metric discovery

The recommended way to achieve this is:

- layered constraints
- extensible schema sections
- typed signal and operator registries
- explicit validation protocol
- versioned experiment manifests

## Principle 1. Use a Three-Layer Manifest

The manifest should be divided into three top-level layers:

```text
manifest
  -> medical_constraints
  -> research_definition
  -> search_config
```

This separation is the most important design decision because each layer has a different owner and a different change cadence.

### `medical_constraints`

This layer is platform- and clinician-controlled.

It defines the medical guardrails for what the search engine is allowed to do.

Typical contents:

- allowed signals
- allowed operators
- formula complexity limits
- allowed structural motifs
- prohibited transformations

Example:

```yaml
medical_constraints:
  allowed_signals:
    - stride_length
    - stride_variability
    - head_bob_amplitude
    - body_length

  allowed_operators:
    - add
    - sub
    - mul
    - div
    - abs
    - ratio

  max_formula_depth: 5
```

This layer exists to:

- block medically meaningless expressions
- control the search space
- preserve interpretability

### `research_definition`

This layer is controlled by the researcher or research agent.

It defines the study-specific question and search scope.

Typical contents:

- research question
- target variable
- cohort definition
- candidate variables
- inclusion and exclusion assumptions

Example:

```yaml
research_definition:
  research_question: "Can gait asymmetry predict early joint pain?"
  target_variable: pain_score
  candidate_variables:
    - stride_length
    - left_stride
    - right_stride
    - stride_variability
```

This layer should be flexible, because it is where new hypotheses are expressed.

### `search_config`

This layer is the compute-controlled algorithm section.

Typical contents:

- search engine
- runtime budget
- population settings
- iteration settings
- loss choice
- selection method
- reproducibility controls

Example:

```yaml
search_config:
  engine: pysr
  population_size: 2000
  generations: 80
  evaluation:
    metric: r2
    cross_validation: 5
```

This layer should be editable by the system without changing the medical meaning of the experiment.

## Principle 2. Use a Signal Ontology, Not Bare Variable Names

The manifest should not rely on plain feature names alone.

Signals should be represented as typed entities with metadata.

Recommended structure:

```yaml
signals:
  - name: stride_length
    type: gait
    unit: body_length_ratio
    reliability: high

  - name: head_bob_amplitude
    type: posture
    unit: radians
    reliability: medium
```

This is important because it allows the platform to:

- track signal provenance
- preserve unit semantics
- filter low-reliability signals
- enforce allowed signal families
- support future ontology-based search policies

For real-world video-derived data, signal ontology is mandatory rather than optional.

## Principle 3. Use an Operator Registry

The manifest should not expose arbitrary math functions directly.

Operators should be referenced through a controlled registry.

Recommended structure:

```yaml
operator_registry:
  add:
    arity: 2
    interpretability: high

  ratio:
    arity: 2
    interpretability: high

  abs:
    arity: 1
    interpretability: high
```

This allows the system to:

- map domain-safe names to actual PySR operators
- classify operators by interpretability and risk
- extend the operator surface without losing control
- support future custom operators in a governed way

If the platform later introduces a domain-specific operator such as `rolling_mean` or `normalized_ratio`, it should be added through the registry rather than inserted ad hoc into experiment files.

## Principle 4. Make Formula Complexity Explicit

Medical symbolic regression should define formula complexity as part of the protocol, not as an implicit tuning choice.

Recommended section:

```yaml
formula_constraints:
  max_depth: 5
  max_nodes: 15
  allowed_structures:
    - linear
    - ratio
    - difference
```

This section should be used to constrain:

- maximum depth
- maximum nodes
- allowable structural motifs
- nesting behavior
- optional monotonicity or safety rules in future versions

Most clinically acceptable formulas are structurally simple. If a candidate requires high symbolic complexity to work, the default assumption should be that it is less suitable for medical deployment.

## Principle 5. Define Validation as Part of the Manifest

The manifest should not describe search alone. It should also describe the required validation protocol.

Recommended structure:

```yaml
validation:
  cross_validation: 5

  stability_test:
    dataset_split: breed

  significance_test:
    p_value_threshold: 0.05
```

This is important because a formula is not useful merely because it fits the training set.

The validation section should support:

- cross-validation
- held-out evaluation
- stability by cohort
- breed generalization checks
- missingness sensitivity
- robustness under noisy conditions
- significance thresholds where scientifically appropriate

Cross-breed generalization is especially important for canine health research and should be a first-class validation dimension.

## Principle 6. Make the Manifest Agent-Generatable

If the research agent is expected to propose experiments, the schema must be straightforward for an agent to generate and for a validator to check.

Recommended metadata:

```yaml
experiment:
  generated_by: research_agent
  timestamp: 2026-03-16
```

Agent-generated manifests should still be governed by:

- schema validation
- signal ontology checks
- operator registry checks
- medical constraint checks

The agent may draft a manifest, but it may not expand beyond the platform-approved medical boundary.

## Principle 7. Treat the Manifest as a Versioned Research Protocol

The manifest should be stored like a protocol artifact:

```text
experiments/
  gait_asymmetry_v1.yaml
  gait_asymmetry_v2.yaml
  fatigue_detection_v1.yaml
```

This is necessary for:

- reproducibility
- auditability
- experiment comparison
- formula comparison across protocol versions
- clear separation between exploratory and validated studies

In a medical AI platform, the manifest is part of the evidence trail.

## Recommended High-Level Schema

The schema should be extensible, but the high-level structure should remain stable.

Recommended shape:

```yaml
experiment:
  experiment_id: gait_pain_discovery_v1
  generated_by: research_agent
  timestamp: 2026-03-16
  manifest_version: 1

medical_constraints:
  allowed_signals:
    - stride_length
    - stride_variability
    - head_bob_amplitude
    - body_length
  allowed_operators:
    - add
    - sub
    - mul
    - div
    - abs
  max_formula_depth: 5

research_definition:
  research_question: "Can gait asymmetry predict early joint pain?"
  target_variable: pain_score
  candidate_variables:
    - stride_length
    - left_stride
    - right_stride
    - stride_variability

signals:
  - name: stride_length
    type: gait
    unit: body_length_ratio
    reliability: high

operator_registry:
  add:
    arity: 2
    interpretability: high
  abs:
    arity: 1
    interpretability: high

formula_constraints:
  max_depth: 5
  max_nodes: 15
  allowed_structures:
    - ratio
    - difference

search_config:
  engine: pysr
  population_size: 1500
  generations: 60

validation:
  metric: r2
  cross_validation: 5
  complexity_penalty: 0.01
```

## Ownership Model

The manifest should make ownership explicit.

Recommended control model:

- `medical_constraints`: platform and medical team
- `research_definition`: researcher or agent
- `search_config`: system and compute layer
- `validation`: shared scientific governance

This ownership split is one of the main reasons the three-layer design works well in practice.

## Design Summary

A good PySR manifest schema should provide:

- medical reasonableness through `medical_constraints`
- research flexibility through `research_definition`
- algorithm tunability through `search_config`
- signal rigor through a `signals` ontology
- operator safety through an `operator_registry`
- interpretability through `formula_constraints`
- clinical reliability through `validation`
- reproducibility through protocol versioning

If these properties hold, the manifest becomes a reliable contract between the research agent, the PySR engine, the validation layer, and the review process.
