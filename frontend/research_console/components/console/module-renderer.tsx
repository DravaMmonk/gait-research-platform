"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { VisualModule } from "@/lib/console-types";

function SummaryCard({ module }: { module: Extract<VisualModule, { type: "summary_card" }> }) {
  return (
    <article className="ui-panel">
      <p className="ui-eyebrow">{module.title}</p>
      <h3 className="ui-panel-title">{module.payload.title}</h3>
      <p className="ui-copy mt-3">{module.payload.summary}</p>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        {module.payload.highlights.map((item) => (
          <div key={item.label} className="ui-section">
            <p className="ui-micro">{item.label}</p>
            <p className="mt-2 text-lg font-semibold">{item.value}</p>
          </div>
        ))}
      </div>
    </article>
  );
}

function TrendChart({ module }: { module: Extract<VisualModule, { type: "trend_chart" }> }) {
  return (
    <article className="ui-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="ui-eyebrow">{module.payload.metric}</p>
          <h3 className="ui-panel-title">{module.title}</h3>
        </div>
        <span className="ui-badge">{module.payload.time_range}</span>
      </div>
      <div className="mt-5 h-72 min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={module.payload.series}>
            <defs>
              <linearGradient id="consoleTrend" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.35} />
                <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="rgba(15, 23, 42, 0.08)" />
            <XAxis dataKey="label" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip />
            <Area type="monotone" dataKey="value" stroke="var(--primary)" strokeWidth={2.5} fill="url(#consoleTrend)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

function MetricTable({ module }: { module: Extract<VisualModule, { type: "metric_table" }> }) {
  return (
    <article className="ui-panel ui-scroll-x">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="ui-eyebrow">{module.payload.metric}</p>
          <h3 className="ui-panel-title">{module.title}</h3>
        </div>
        {module.payload.sort ? <span className="ui-badge">{module.payload.sort}</span> : null}
      </div>
      <table className="mt-5 w-full min-w-[30rem] text-left text-sm">
        <thead>
          <tr className="border-b border-[var(--border)] text-[var(--muted-foreground)]">
            {module.payload.columns.map((column) => (
              <th key={column.key} className="pb-3 font-medium">
                {column.label}
              </th>
            ))}
            <th className="pb-3 font-medium">Type</th>
          </tr>
        </thead>
        <tbody>
          {module.payload.rows.map((row, index) => (
            <tr key={`${index}-${row.values[module.payload.columns[0]?.key ?? "row"]}`} className="border-b border-[var(--border)]/70">
              {module.payload.columns.map((column) => (
                <td key={column.key} className="py-3 pr-4">
                  {String(row.values[column.key] ?? "n/a")}
                </td>
              ))}
              <td className="py-3">{row.raw ? "raw" : row.derived ? "derived" : "mixed"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}

function EvidencePanel({ module }: { module: Extract<VisualModule, { type: "evidence_panel" }> }) {
  return (
    <article className="ui-panel">
      <p className="ui-eyebrow">{module.payload.review_status}</p>
      <h3 className="ui-panel-title">{module.title}</h3>
      <dl className="mt-5 space-y-4">
        <div>
          <dt className="ui-micro">Confidence</dt>
          <dd className="ui-copy mt-2">{module.payload.confidence}</dd>
        </div>
        <div>
          <dt className="ui-micro">Missingness</dt>
          <dd className="ui-copy mt-2">{module.payload.missingness}</dd>
        </div>
        <div>
          <dt className="ui-micro">Provenance</dt>
          <dd className="ui-copy mt-2">{module.payload.provenance}</dd>
        </div>
      </dl>
      <ul className="mt-5 space-y-2">
        {module.payload.sources.map((source) => (
          <li key={`${source.kind}-${source.reference}`} className="ui-section">
            <p className="ui-micro">{source.label}</p>
            <p className="mt-2 text-sm font-medium">{source.reference}</p>
          </li>
        ))}
      </ul>
    </article>
  );
}

function FormulaCard({ module }: { module: Extract<VisualModule, { type: "formula_explanation_card" }> }) {
  return (
    <article className="ui-panel">
      <p className="ui-eyebrow">{module.payload.formula_id}</p>
      <h3 className="ui-panel-title">{module.title}</h3>
      <pre className="ui-code mt-5">{module.payload.expression}</pre>
      <p className="ui-copy mt-5">{module.payload.interpretation}</p>
      <ul className="mt-5 space-y-2">
        {module.payload.assumptions.map((assumption) => (
          <li key={assumption} className="ui-section text-sm">
            {assumption}
          </li>
        ))}
      </ul>
    </article>
  );
}

function VideoPanel({ module }: { module: Extract<VisualModule, { type: "video_panel" }> }) {
  return (
    <article className="ui-panel">
      <p className="ui-eyebrow">{module.payload.asset_id}</p>
      <h3 className="ui-panel-title">{module.payload.title}</h3>
      <div className="mt-5 flex aspect-video items-center justify-center rounded-[1.25rem] border border-dashed border-[var(--border-strong)] bg-[var(--muted)] text-sm text-[var(--muted-foreground)]">
        Video panel placeholder
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="ui-badge">{module.payload.timestamp_range}</span>
        {module.payload.related_metrics.map((metric) => (
          <span key={metric} className="ui-badge">
            {metric}
          </span>
        ))}
      </div>
    </article>
  );
}

function ComparisonCards({ module }: { module: Extract<VisualModule, { type: "comparison_cards" }> }) {
  return (
    <article className="ui-panel">
      <p className="ui-eyebrow">{module.title}</p>
      <h3 className="ui-panel-title">{module.payload.title}</h3>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {module.payload.items.map((item) => (
          <div key={item.label} className="ui-section">
            <p className="ui-micro">{item.label}</p>
            <p className="mt-2 text-2xl font-semibold">{item.value}</p>
            {item.delta ? <p className="mt-1 text-sm text-[var(--muted-foreground)]">{item.delta}</p> : null}
          </div>
        ))}
      </div>
    </article>
  );
}

export function ModuleRenderer({ module }: { module: VisualModule }) {
  switch (module.type) {
    case "summary_card":
      return <SummaryCard module={module} />;
    case "trend_chart":
      return <TrendChart module={module} />;
    case "metric_table":
      return <MetricTable module={module} />;
    case "evidence_panel":
      return <EvidencePanel module={module} />;
    case "formula_explanation_card":
      return <FormulaCard module={module} />;
    case "video_panel":
      return <VideoPanel module={module} />;
    case "comparison_cards":
      return <ComparisonCards module={module} />;
    default:
      return null;
  }
}
