from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from research_tools.common.cli import run_cli
from research_tools.symbolic.io_models import PySRManifest


def load_manifest(path: str) -> dict[str, Any]:
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    if input_path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    else:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest input must deserialize into a mapping.")
    return payload


def summarize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    model = PySRManifest.model_validate(manifest)

    signal_names = {signal.name for signal in model.signals}
    allowed_signals = set(model.medical_constraints.allowed_signals)
    candidate_variables = set(model.research_definition.candidate_variables)
    operator_names = set(model.operator_registry)
    allowed_operators = set(model.medical_constraints.allowed_operators)

    warnings: list[str] = []
    if model.search_config.engine.lower() != "pysr":
        warnings.append("search_config.engine is not set to 'pysr'.")
    if candidate_variables - allowed_signals:
        warnings.append(
            "research_definition.candidate_variables contains values outside medical_constraints.allowed_signals."
        )
    if candidate_variables - signal_names:
        warnings.append("research_definition.candidate_variables contains values missing from signals ontology.")
    if allowed_operators - operator_names:
        warnings.append("medical_constraints.allowed_operators contains values missing from operator_registry.")
    if model.formula_constraints.max_depth and model.medical_constraints.max_formula_depth:
        if model.formula_constraints.max_depth > model.medical_constraints.max_formula_depth:
            warnings.append("formula_constraints.max_depth exceeds medical_constraints.max_formula_depth.")
    if model.validation.cross_validation is not None and model.validation.cross_validation < 3:
        warnings.append("validation.cross_validation is below the recommended minimum of 3 folds.")

    low_reliability = [signal.name for signal in model.signals if (signal.reliability or "").lower() == "low"]
    if low_reliability:
        warnings.append(f"Low-reliability signals present: {', '.join(low_reliability)}.")

    summary = {
        "experiment_id": model.experiment.experiment_id,
        "research_question": model.research_definition.research_question,
        "target_variable": model.research_definition.target_variable,
        "signal_count": len(model.signals),
        "candidate_variable_count": len(model.research_definition.candidate_variables),
        "allowed_operator_count": len(model.medical_constraints.allowed_operators),
        "cross_validation_folds": model.validation.cross_validation,
        "max_formula_depth": model.medical_constraints.max_formula_depth,
        "engine": model.search_config.engine,
    }
    ownership = [
        {"section": "medical_constraints", "owner": "platform_and_medical_team"},
        {"section": "research_definition", "owner": "researcher_or_agent"},
        {"section": "search_config", "owner": "system"},
        {"section": "validation", "owner": "shared_scientific_governance"},
    ]
    update_targets = [
        {
            "section": "medical_constraints",
            "should_update_when": "medical governance changes signal or operator policy",
        },
        {
            "section": "research_definition",
            "should_update_when": "the research question, target, or candidate variables change",
        },
        {
            "section": "search_config",
            "should_update_when": "the compute team tunes PySR search behavior without changing study meaning",
        },
        {
            "section": "validation",
            "should_update_when": "the evidence threshold or cohort stability protocol changes",
        },
    ]
    sections = {
        "medical_constraints": model.medical_constraints.model_dump(mode="json"),
        "research_definition": model.research_definition.model_dump(mode="json"),
        "signals": [signal.model_dump(mode="json") for signal in model.signals],
        "operator_registry": {name: spec.model_dump(mode="json") for name, spec in model.operator_registry.items()},
        "formula_constraints": model.formula_constraints.model_dump(mode="json"),
        "search_config": model.search_config.model_dump(mode="json"),
        "validation": model.validation.model_dump(mode="json"),
    }
    markdown = build_markdown(summary=summary, warnings=warnings, ownership=ownership)
    mermaid = build_mermaid()
    return {
        "summary": summary,
        "warnings": warnings,
        "ownership": ownership,
        "update_targets": update_targets,
        "sections": sections,
        "markdown": markdown,
        "mermaid": mermaid,
    }


def build_markdown(*, summary: dict[str, Any], warnings: list[str], ownership: list[dict[str, str]]) -> str:
    lines = [
        f"# Manifest Review: {summary['experiment_id']}",
        "",
        f"- Research question: {summary['research_question']}",
        f"- Target variable: {summary['target_variable']}",
        f"- Search engine: {summary['engine']}",
        f"- Signals: {summary['signal_count']}",
        f"- Candidate variables: {summary['candidate_variable_count']}",
        f"- Allowed operators: {summary['allowed_operator_count']}",
        f"- Cross-validation folds: {summary['cross_validation_folds']}",
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


def build_mermaid() -> str:
    return "\n".join(
        [
            "flowchart LR",
            '    A["medical_constraints"] --> B["research_definition"]',
            '    B --> C["search_config"]',
            '    C --> D["PySR engine"]',
            '    D --> E["validation"]',
            '    E --> F["human review and update"]',
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    summary_items = "".join(
        f"<li><strong>{html.escape(str(key))}</strong>: {html.escape(str(value))}</li>"
        for key, value in report["summary"].items()
    )
    warning_items = "".join(
        f"<li>{html.escape(warning)}</li>" for warning in report["warnings"]
    ) or "<li>No schema consistency warnings detected.</li>"
    ownership_rows = "".join(
        "<tr><td>{section}</td><td>{owner}</td></tr>".format(
            section=html.escape(item["section"]),
            owner=html.escape(item["owner"]),
        )
        for item in report["ownership"]
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Manifest Review: {html.escape(report["summary"]["experiment_id"])}</title>
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2937; }}
      .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
      .card {{ border: 1px solid #d1d5db; border-radius: 12px; padding: 16px; background: #f9fafb; }}
      table {{ border-collapse: collapse; width: 100%; }}
      th, td {{ text-align: left; border-bottom: 1px solid #e5e7eb; padding: 8px 0; }}
      pre {{ background: #111827; color: #f9fafb; padding: 16px; border-radius: 12px; overflow: auto; }}
    </style>
  </head>
  <body>
    <h1>Manifest Review</h1>
    <div class="grid">
      <section class="card">
        <h2>Summary</h2>
        <ul>{summary_items}</ul>
      </section>
      <section class="card">
        <h2>Warnings</h2>
        <ul>{warning_items}</ul>
      </section>
    </div>
    <section class="card">
      <h2>Ownership</h2>
      <table>
        <thead><tr><th>Section</th><th>Owner</th></tr></thead>
        <tbody>{ownership_rows}</tbody>
      </table>
    </section>
    <section class="card">
      <h2>Review Markdown</h2>
      <pre>{html.escape(report["markdown"])}</pre>
    </section>
    <section class="card">
      <h2>Mermaid</h2>
      <pre>{html.escape(report["mermaid"])}</pre>
    </section>
  </body>
</html>
"""


def visualize_manifest(input_path: str, output_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = load_manifest(input_path)
    report = summarize_manifest(manifest)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    html_output = None
    if config is None or config.get("write_html", True):
        html_output = Path(config["html_output_path"]) if config and config.get("html_output_path") else output.with_suffix(".html")
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html_output.write_text(render_html(report), encoding="utf-8")

    return {
        "tool": "visualize_manifest",
        "report_path": str(output),
        "html_path": str(html_output) if html_output else None,
        "warning_count": len(report["warnings"]),
        "summary": report["summary"],
    }


if __name__ == "__main__":
    run_cli("visualize_manifest", visualize_manifest)
