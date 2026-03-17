from __future__ import annotations

from typing import Any


def summarize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    signals = manifest.get("signals") or []
    candidate_variables = ((manifest.get("research_definition") or {}).get("candidate_variables") or [])
    operator_registry = manifest.get("operator_registry") or {}
    constraints = manifest.get("medical_constraints") or {}
    validation = manifest.get("validation") or {}
    search_config = manifest.get("search_config") or {}
    research_definition = manifest.get("research_definition") or {}
    experiment = manifest.get("experiment") or {}

    signal_names = {item.get("name") for item in signals if isinstance(item, dict) and item.get("name")}
    allowed_signals = set(constraints.get("allowed_signals") or [])
    allowed_operators = set(constraints.get("allowed_operators") or [])
    operator_names = set(operator_registry)

    warnings: list[str] = []
    if str(search_config.get("engine") or "").lower() != "pysr":
        warnings.append("search_config.engine is not set to 'pysr'.")
    if set(candidate_variables) - allowed_signals:
        warnings.append("research_definition.candidate_variables contains values outside medical_constraints.allowed_signals.")
    if set(candidate_variables) - signal_names:
        warnings.append("research_definition.candidate_variables contains values missing from signals ontology.")
    if allowed_operators - operator_names:
        warnings.append("medical_constraints.allowed_operators contains values missing from operator_registry.")
    if (validation.get("cross_validation") or 0) and int(validation["cross_validation"]) < 3:
        warnings.append("validation.cross_validation is below the recommended minimum of 3 folds.")

    summary = {
        "experiment_id": experiment.get("experiment_id"),
        "research_question": research_definition.get("research_question"),
        "target_variable": research_definition.get("target_variable"),
        "signal_count": len(signals),
        "candidate_variable_count": len(candidate_variables),
        "allowed_operator_count": len(allowed_operators),
        "cross_validation_folds": validation.get("cross_validation"),
        "max_formula_depth": constraints.get("max_formula_depth"),
        "engine": search_config.get("engine"),
    }
    ownership = [
        {"section": "medical_constraints", "owner": "platform_and_medical_team"},
        {"section": "research_definition", "owner": "researcher_or_agent"},
        {"section": "search_config", "owner": "system"},
        {"section": "validation", "owner": "shared_scientific_governance"},
    ]
    return {
        "summary": summary,
        "warnings": warnings,
        "ownership": ownership,
        "update_targets": [
            {"section": "medical_constraints", "should_update_when": "medical governance changes signal or operator policy"},
            {"section": "research_definition", "should_update_when": "the research question, target, or candidate variables change"},
            {"section": "search_config", "should_update_when": "the compute team tunes search behavior without changing study meaning"},
            {"section": "validation", "should_update_when": "the evidence threshold or cohort stability protocol changes"},
        ],
        "sections": {
            "medical_constraints": constraints,
            "research_definition": research_definition,
            "signals": signals,
            "operator_registry": operator_registry,
            "formula_constraints": manifest.get("formula_constraints") or {},
            "search_config": search_config,
            "validation": validation,
        },
        "markdown": _build_markdown(summary=summary, warnings=warnings, ownership=ownership),
        "mermaid": _build_mermaid(),
    }


def _build_markdown(*, summary: dict[str, Any], warnings: list[str], ownership: list[dict[str, str]]) -> str:
    lines = [
        f"# Manifest Review: {summary.get('experiment_id')}",
        "",
        f"- Research question: {summary.get('research_question')}",
        f"- Target variable: {summary.get('target_variable')}",
        f"- Search engine: {summary.get('engine')}",
        f"- Signals: {summary.get('signal_count')}",
        f"- Candidate variables: {summary.get('candidate_variable_count')}",
        f"- Allowed operators: {summary.get('allowed_operator_count')}",
        f"- Cross-validation folds: {summary.get('cross_validation_folds')}",
        "",
        "## Ownership",
    ]
    lines.extend([f"- {item['section']}: {item['owner']}" for item in ownership])
    lines.append("")
    lines.append("## Checks")
    if warnings:
        lines.extend([f"- Warning: {warning}" for warning in warnings])
    else:
        lines.append("- No schema consistency warnings detected.")
    return "\n".join(lines)


def _build_mermaid() -> str:
    return "\n".join(
        [
            "flowchart LR",
            '    A["medical_constraints"] --> B["research_definition"]',
            '    B --> C["search_config"]',
            '    C --> D["search engine"]',
            '    D --> E["validation"]',
            '    E --> F["human review and update"]',
        ]
    )

