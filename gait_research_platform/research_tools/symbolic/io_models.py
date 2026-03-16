from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExperimentMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    experiment_id: str
    generated_by: str | None = None
    timestamp: str | None = None
    manifest_version: int | str = 1
    status: str | None = None


class MedicalConstraints(BaseModel):
    model_config = ConfigDict(extra="allow")

    allowed_signals: list[str] = Field(default_factory=list)
    allowed_operators: list[str] = Field(default_factory=list)
    max_formula_depth: int | None = None


class ResearchDefinition(BaseModel):
    model_config = ConfigDict(extra="allow")

    research_question: str
    target_variable: str
    target_type: str | None = None
    candidate_variables: list[str] = Field(default_factory=list)


class SignalSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    type: str | None = None
    unit: str | None = None
    reliability: str | None = None


class OperatorSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    arity: int | None = None
    interpretability: str | None = None
    pysr_name: str | None = None


class FormulaConstraints(BaseModel):
    model_config = ConfigDict(extra="allow")

    max_depth: int | None = None
    max_nodes: int | None = None
    allowed_structures: list[str] = Field(default_factory=list)
    nested_constraints: dict[str, Any] = Field(default_factory=dict)


class SearchConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    engine: str = "pysr"
    population_size: int | None = None
    generations: int | None = None
    model_selection: str | None = None
    binary_operators: list[str] = Field(default_factory=list)
    unary_operators: list[str] = Field(default_factory=list)
    maxsize: int | None = None
    warm_start: bool | None = None
    random_state: int | None = None
    deterministic: bool | None = None
    parallelism: str | None = None
    complexity_penalty: float | None = None


class ValidationSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    metric: str | None = None
    cross_validation: int | None = None


class PySRManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    experiment: ExperimentMetadata
    medical_constraints: MedicalConstraints
    research_definition: ResearchDefinition
    signals: list[SignalSpec] = Field(default_factory=list)
    operator_registry: dict[str, OperatorSpec] = Field(default_factory=dict)
    formula_constraints: FormulaConstraints = Field(default_factory=FormulaConstraints)
    search_config: SearchConfig
    validation: ValidationSpec = Field(default_factory=ValidationSpec)
