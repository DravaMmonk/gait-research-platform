"use client";

import { useId } from "react";
import { VisualModule } from "@/lib/console-types";

function buildSparklinePoints(series: Array<{ label: string; value: number }>) {
  if (!series.length) {
    return "";
  }

  const width = 100;
  const height = 100;
  const max = Math.max(...series.map((item) => item.value));
  const min = Math.min(...series.map((item) => item.value));
  const range = max - min || 1;

  return series
    .map((item, index) => {
      const x = series.length === 1 ? width / 2 : (index / (series.length - 1)) * width;
      const y = height - ((item.value - min) / range) * height;
      return `${x},${y}`;
    })
    .join(" ");
}

function buildAreaPath(series: Array<{ label: string; value: number }>) {
  if (!series.length) {
    return "";
  }

  const points = buildSparklinePoints(series)
    .split(" ")
    .filter(Boolean);

  if (!points.length) {
    return "";
  }

  const first = points[0].split(",");
  const last = points[points.length - 1].split(",");
  return `M ${first[0]} 100 L ${points.join(" L ")} L ${last[0]} 100 Z`;
}

function SummaryCard({
  module,
  compact,
}: {
  module: Extract<VisualModule, { type: "summary_card" }>;
  compact?: boolean;
}) {
  return (
    <article className={compact ? "module-card module-card-compact" : "ui-panel"}>
      <p className={compact ? "module-kicker" : "ui-eyebrow"}>{module.title}</p>
      <h3 className={compact ? "module-title" : "ui-panel-title"}>{module.payload.title}</h3>
      <p className={compact ? "module-copy" : "ui-copy mt-3"}>{module.payload.summary}</p>
      <div className={compact ? "module-grid" : "mt-5 grid gap-3 sm:grid-cols-3"}>
        {module.payload.highlights.map((item) => (
          <div key={item.label} className={compact ? "module-subcard" : "ui-section"}>
            <p className={compact ? "module-subtle" : "ui-micro"}>{item.label}</p>
            <p className="mt-2 text-lg font-semibold">{item.value}</p>
          </div>
        ))}
      </div>
    </article>
  );
}

function TrendChart({ module, compact }: { module: Extract<VisualModule, { type: "trend_chart" }>; compact?: boolean }) {
  const gradientId = useId();
  const min = Math.min(...module.payload.series.map((item) => item.value));
  const max = Math.max(...module.payload.series.map((item) => item.value));
  const points = buildSparklinePoints(module.payload.series);
  const areaPath = buildAreaPath(module.payload.series);

  return (
    <article className={compact ? "module-card module-card-compact" : "ui-panel"}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className={compact ? "module-kicker" : "ui-eyebrow"}>{module.payload.metric}</p>
          <h3 className={compact ? "module-title" : "ui-panel-title"}>{module.title}</h3>
        </div>
        <span className={compact ? "module-pill" : "ui-badge"}>{module.payload.time_range}</span>
      </div>
      <div className={compact ? "mt-4 min-w-0" : "mt-5 min-w-0"}>
        <div className="rounded-[0.5rem] border border-[var(--border)] bg-[var(--panel-muted)] p-4">
          <div className="flex items-end justify-between text-xs text-[var(--muted-foreground)]">
            <span>{max.toFixed(1)}</span>
            <span>{module.payload.unit}</span>
          </div>
          <div className="mt-3 h-44 w-full">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full overflow-visible">
              <defs>
                <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
                  <stop offset="5%" stopColor="var(--primary)" stopOpacity="0.3" />
                  <stop offset="95%" stopColor="var(--primary)" stopOpacity="0.04" />
                </linearGradient>
              </defs>
              <path d={areaPath} fill={`url(#${gradientId})`} />
              <polyline
                fill="none"
                stroke="var(--primary)"
                strokeWidth="2.5"
                strokeLinejoin="round"
                strokeLinecap="round"
                points={points}
              />
            </svg>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-[var(--muted-foreground)]">
            <span>{module.payload.series[0]?.label}</span>
            <span>{module.payload.series[module.payload.series.length - 1]?.label}</span>
          </div>
          <div className="mt-4 grid gap-2 sm:grid-cols-4">
            {module.payload.series.map((item) => (
              <div key={item.label} className="rounded-[0.5rem] border border-[var(--border)] bg-[var(--panel)] px-3 py-2">
                <p className="text-[0.69rem] font-semibold uppercase tracking-[0.12em] text-[var(--muted-foreground)]">{item.label}</p>
                <p className="mt-1 text-sm font-semibold text-[var(--foreground)]">{item.value}</p>
              </div>
            ))}
          </div>
          <div className="mt-3 text-xs text-[var(--muted-foreground)]">Range: {min.toFixed(1)} to {max.toFixed(1)}</div>
        </div>
      </div>
    </article>
  );
}

function MetricTable({ module, compact }: { module: Extract<VisualModule, { type: "metric_table" }>; compact?: boolean }) {
  return (
    <article className={compact ? "module-card module-card-compact ui-stable-panel ui-stable-scroll-x" : "ui-panel ui-stable-panel ui-stable-scroll-x"}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className={compact ? "module-kicker" : "ui-eyebrow"}>{module.payload.metric}</p>
          <h3 className={compact ? "module-title" : "ui-panel-title"}>{module.title}</h3>
        </div>
        {module.payload.sort ? <span className={compact ? "module-pill" : "ui-badge"}>{module.payload.sort}</span> : null}
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

function EvidencePanel({ module, compact }: { module: Extract<VisualModule, { type: "evidence_panel" }>; compact?: boolean }) {
  return (
    <article className={compact ? "module-card module-card-compact" : "ui-panel"}>
      <p className={compact ? "module-kicker" : "ui-eyebrow"}>{module.payload.review_status}</p>
      <h3 className={compact ? "module-title" : "ui-panel-title"}>{module.title}</h3>
      <dl className="mt-5 space-y-4">
        <div>
          <dt className={compact ? "module-subtle" : "ui-micro"}>Confidence</dt>
          <dd className={compact ? "module-copy" : "ui-copy mt-2"}>{module.payload.confidence}</dd>
        </div>
        <div>
          <dt className={compact ? "module-subtle" : "ui-micro"}>Missingness</dt>
          <dd className={compact ? "module-copy" : "ui-copy mt-2"}>{module.payload.missingness}</dd>
        </div>
        <div>
          <dt className={compact ? "module-subtle" : "ui-micro"}>Provenance</dt>
          <dd className={compact ? "module-copy" : "ui-copy mt-2"}>{module.payload.provenance}</dd>
        </div>
      </dl>
      <ul className="mt-5 space-y-2">
        {module.payload.sources.map((source) => (
          <li key={`${source.kind}-${source.reference}`} className={compact ? "module-subcard" : "ui-section"}>
            <p className={compact ? "module-subtle" : "ui-micro"}>{source.label}</p>
            <p className="mt-2 text-sm font-medium">{source.reference}</p>
          </li>
        ))}
      </ul>
    </article>
  );
}

function FormulaCard({ module, compact }: { module: Extract<VisualModule, { type: "formula_explanation_card" }>; compact?: boolean }) {
  return (
    <article className={compact ? "module-card module-card-compact" : "ui-panel"}>
      <p className={compact ? "module-kicker" : "ui-eyebrow"}>{module.payload.formula_id}</p>
      <h3 className={compact ? "module-title" : "ui-panel-title"}>{module.title}</h3>
      <pre className={compact ? "module-code" : "ui-code mt-5"}>{module.payload.expression}</pre>
      <p className={compact ? "module-copy" : "ui-copy mt-5"}>{module.payload.interpretation}</p>
      <ul className="mt-5 space-y-2">
        {module.payload.assumptions.map((assumption) => (
          <li key={assumption} className={compact ? "module-subcard text-sm" : "ui-section text-sm"}>
            {assumption}
          </li>
        ))}
      </ul>
    </article>
  );
}

function VideoPanel({ module, compact }: { module: Extract<VisualModule, { type: "video_panel" }>; compact?: boolean }) {
  return (
    <article className={compact ? "module-card module-card-compact" : "ui-panel"}>
      <p className={compact ? "module-kicker" : "ui-eyebrow"}>{module.payload.asset_id}</p>
      <h3 className={compact ? "module-title" : "ui-panel-title"}>{module.payload.title}</h3>
      <div className="mt-5 flex aspect-video items-center justify-center rounded-[0.5rem] border border-dashed border-[var(--border-strong)] bg-[var(--panel-muted)] text-sm text-[var(--muted-foreground)]">
        Video panel placeholder
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className={compact ? "module-pill" : "ui-badge"}>{module.payload.timestamp_range}</span>
        {module.payload.related_metrics.map((metric) => (
          <span key={metric} className={compact ? "module-pill" : "ui-badge"}>
            {metric}
          </span>
        ))}
      </div>
    </article>
  );
}

function ComparisonCards({ module, compact }: { module: Extract<VisualModule, { type: "comparison_cards" }>; compact?: boolean }) {
  return (
    <article className={compact ? "module-card module-card-compact" : "ui-panel"}>
      <p className={compact ? "module-kicker" : "ui-eyebrow"}>{module.title}</p>
      <h3 className={compact ? "module-title" : "ui-panel-title"}>{module.payload.title}</h3>
      <div className={compact ? "module-grid" : "mt-5 grid gap-3 sm:grid-cols-2"}>
        {module.payload.items.map((item) => (
          <div key={item.label} className={compact ? "module-subcard" : "ui-section"}>
            <p className={compact ? "module-subtle" : "ui-micro"}>{item.label}</p>
            <p className="mt-2 text-2xl font-semibold">{item.value}</p>
            {item.delta ? <p className="mt-1 text-sm text-[var(--muted-foreground)]">{item.delta}</p> : null}
          </div>
        ))}
      </div>
    </article>
  );
}

export function ModuleRenderer({ module, compact = false }: { module: VisualModule; compact?: boolean }) {
  switch (module.type) {
    case "summary_card":
      return <SummaryCard module={module} compact={compact} />;
    case "trend_chart":
      return <TrendChart module={module} compact={compact} />;
    case "metric_table":
      return <MetricTable module={module} compact={compact} />;
    case "evidence_panel":
      return <EvidencePanel module={module} compact={compact} />;
    case "formula_explanation_card":
      return <FormulaCard module={module} compact={compact} />;
    case "video_panel":
      return <VideoPanel module={module} compact={compact} />;
    case "comparison_cards":
      return <ComparisonCards module={module} compact={compact} />;
    default:
      return null;
  }
}
