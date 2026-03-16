# Medical Symbolic Regression Principles

## Intent

This document defines the primary goal, operating principles, and validation boundaries for the Hound Forward medical symbolic regression research system.

The system exists to discover interpretable, reproducible, and clinically reviewable health metrics from multimodal canine data. It is a research system for metric discovery, not an autonomous diagnostic engine.

## Primary Goal

The primary goal is to identify candidate digital biomarkers that:

- are expressed as explicit mathematical formulas
- can be reproduced across datasets and institutions
- remain interpretable to clinicians and researchers
- can be validated against biological mechanisms and clinical outcomes
- can be deployed into real-world monitoring workflows only after review

The platform should help answer questions such as:

- can movement asymmetry predict early joint pain
- can posture instability indicate fatigue or discomfort
- can behavioral signals correlate with stress or reduced wellbeing

## Why Symbolic Regression

Symbolic regression is the preferred discovery method when the platform needs:

- transparent formulas instead of black-box scores
- flexible search over candidate mathematical structures
- explicit comparison between simplicity and predictive value
- scientific hypotheses that can be challenged by domain experts

The desired output is not merely a score. The desired output is a formula with evidence, assumptions, and a clear interpretation.

## Research System Model

The research loop is:

```text
research question
  -> candidate variable set
  -> constrained symbolic search
  -> statistical ranking
  -> LLM interpretation
  -> clinician review
  -> controlled downstream adoption
```

Each stage has a different responsibility:

- the research question defines the target outcome and cohort
- the LLM proposes a reasonable variable space and explains results
- the symbolic regression engine searches the formula space
- the statistical layer ranks and filters candidate formulas
- the clinician decides whether a formula is biologically plausible and useful

## Core Principles

### 1. Clinical interpretability over raw model power

Candidate formulas must stay understandable by researchers and clinicians. If a formula performs well but cannot be explained credibly, it should not be promoted.

### 2. Controlled variable space

The search space must use validated and traceable inputs only. Approved variables may include:

- gait metrics
- posture measurements
- body proportions
- behavioral indicators
- physiological metadata
- environmental factors

Unvalidated, weakly defined, or noisy variables should be excluded from primary discovery runs.

### 3. Restricted formula grammar

The search grammar must be constrained for interpretability and robustness.

Preferred operator families include:

- `+`
- `-`
- `*`
- `/`
- `abs`
- bounded ratios
- simple aggregations such as `mean`

The system should avoid unnecessary expression depth, unstable transforms, and highly complex functional forms unless there is a strong scientific justification.

### 4. Accuracy is necessary but insufficient

A formula is not valuable just because it fits a dataset. Candidate formulas must also be judged on:

- cross-validation performance
- stability across datasets and cohorts
- sensitivity to input noise
- robustness to missing variables
- simplicity

### 5. Clinical plausibility is a hard gate

Statistical quality alone does not make a formula medically meaningful. A candidate metric must be reviewed against plausible biological or behavioral mechanisms before it is considered for adoption.

### 6. Real-world validation matters

Metrics that perform well in controlled datasets must be tested against owner-collected, real-world data before platform adoption. Real-world conditions include:

- variable lighting
- incomplete metadata
- inconsistent camera placement
- signal noise
- incomplete or partial observations

### 7. Reproducibility is mandatory

Every formula proposal must be reproducible from versioned inputs, search configuration, and evaluation outputs. Discovery without reproducibility is not acceptable.

### 8. Auditability by design

The platform must preserve a trace of:

- research question
- approved variable set
- search constraints
- dataset and cohort definitions
- formula candidates
- evaluation metrics
- interpretation notes
- review verdicts

## Operational Boundaries

### LLM responsibilities

The LLM research agent may:

- reformulate a research question into a search plan
- propose candidate variable sets
- summarize top formulas
- explain formula meaning in plain language
- generate follow-up hypotheses and experiment recommendations

The LLM research agent may not:

- invent clinical claims without evidence
- bypass statistical evaluation
- bypass clinician review
- promote a formula to production on narrative confidence alone

### Symbolic regression engine responsibilities

The symbolic regression engine is responsible for:

- searching the approved formula space
- scoring candidate equations against labeled outcomes
- exposing ranked candidates with evaluation evidence

It should not be treated as a source of truth by itself. It is a search mechanism inside a governed research workflow.

### Clinician responsibilities

Clinical reviewers are the final authority on:

- plausibility
- usefulness
- acceptable interpretation
- safe deployment scope

## Validation Standard

A candidate formula should not advance unless it passes all of the following categories:

1. Data validity
   The dataset, labels, and cohort definition are documented and appropriate for the research question.
2. Statistical validity
   The formula shows acceptable predictive behavior under cross-validation and cohort comparison.
3. Robustness
   The formula remains usable under realistic signal degradation and partial variable availability.
4. Interpretability
   The formula can be explained clearly without hidden latent structure.
5. Clinical review
   A domain expert judges the formula plausible and potentially useful.
6. Field validation
   The formula is tested on real-world data before broader adoption.

## Adoption Rules

Formulas discovered by this system should move through staged status levels:

- candidate
- statistically validated
- clinician reviewed
- field validated
- platform approved

No formula should be presented as a diagnostic conclusion unless it has passed the appropriate regulatory, scientific, and clinical review processes for that use case.

## Non-Goals

This system is not intended to:

- replace veterinarians
- produce opaque risk scores without explanation
- optimize only for benchmark accuracy
- deploy unreviewed formulas directly into production decisions
- treat correlation alone as clinical truth

## Design Consequences for the Platform

The platform should therefore support:

- versioned variable libraries
- constrained formula grammars
- reproducible search manifests
- ranked evidence bundles for each formula
- explicit review workflows
- separation between discovery, validation, and deployment

This keeps Hound Forward aligned with its intended role: an evidence-seeking canine health research platform that discovers interpretable digital biomarkers under scientific and clinical governance.
