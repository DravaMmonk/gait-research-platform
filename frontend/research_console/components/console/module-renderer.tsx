"use client";

import { type ReactNode, useId } from "react";
import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/ui/panel";
import { VisualModule } from "@/lib/console-types";
import { cn } from "@/lib/utils";

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

function ModuleFrame({
  compact,
  children,
  className,
}: {
  compact?: boolean;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Panel tone="default" padding={compact ? "compact" : "default"} className={cn("min-w-0", className)}>
      {children}
    </Panel>
  );
}

function ModuleEyebrow({ children }: { children: ReactNode }) {
  return <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{children}</p>;
}

function ModuleTitle({ children }: { children: ReactNode }) {
  return <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-foreground">{children}</h3>;
}

function ModuleBodyCopy({ children }: { children: ReactNode }) {
  return <p className="mt-3 text-sm leading-6 text-muted-foreground">{children}</p>;
}

function SummaryCard({
  module,
  compact,
}: {
  module: Extract<VisualModule, { type: "summary_card" }>;
  compact?: boolean;
}) {
  return (
    <ModuleFrame compact={compact}>
      <ModuleEyebrow>{module.title}</ModuleEyebrow>
      <ModuleTitle>{module.payload.title}</ModuleTitle>
      <ModuleBodyCopy>{module.payload.summary}</ModuleBodyCopy>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        {module.payload.highlights.map((item) => (
          <Panel key={item.label} tone="subtle" padding="compact" className="min-w-0">
            <ModuleEyebrow>{item.label}</ModuleEyebrow>
            <p className="mt-2 text-lg font-semibold text-foreground">{item.value}</p>
          </Panel>
        ))}
      </div>
    </ModuleFrame>
  );
}

function ModuleMetaBadge({ children }: { children: ReactNode }) {
  return (
    <Badge variant="outline" className="rounded-full px-3 py-1 text-[0.68rem] tracking-[0.12em]">
      {children}
    </Badge>
  );
}

function MetricCell({ label, value }: { label: string; value: number | string }) {
  return (
    <Panel tone="subtle" padding="compact" className="min-w-0">
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold text-foreground">{value}</p>
    </Panel>
  );
}

function DefinitionItem({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="space-y-2">
      <ModuleEyebrow>{label}</ModuleEyebrow>
      <div className="text-sm leading-6 text-foreground">{value}</div>
    </div>
  );
}

function AssumptionList({ assumptions }: { assumptions: string[] }) {
  return (
    <ul className="mt-5 space-y-2">
      {assumptions.map((assumption) => (
        <li key={assumption}>
          <Panel tone="subtle" padding="compact" className="text-sm">
            {assumption}
          </Panel>
        </li>
      ))}
    </ul>
  );
}

function ComparisonItem({ label, value, delta }: { label: string; value: string; delta?: string | null }) {
  return (
    <Panel tone="subtle" padding="compact" className="min-w-0">
      <ModuleEyebrow>{label}</ModuleEyebrow>
      <p className="mt-2 text-2xl font-semibold text-foreground">{value}</p>
      {delta ? <p className="mt-1 text-sm text-muted-foreground">{delta}</p> : null}
    </Panel>
  );
}

function SourceItem({ label, reference }: { label: string; reference: string }) {
  return (
    <Panel tone="subtle" padding="compact" className="min-w-0">
      <ModuleEyebrow>{label}</ModuleEyebrow>
      <p className="mt-2 text-sm font-medium text-foreground">{reference}</p>
    </Panel>
  );
}

function ModuleCodeBlock({ value }: { value: string }) {
  return (
    <pre className="mt-5 overflow-x-auto rounded-[calc(var(--radius)+1px)] border border-slate-800 bg-slate-950 p-4 font-mono text-[0.84rem] text-slate-100">
      {value}
    </pre>
  );
}

function TrendChart({ module, compact }: { module: Extract<VisualModule, { type: "trend_chart" }>; compact?: boolean }) {
  const gradientId = useId();
  const min = Math.min(...module.payload.series.map((item) => item.value));
  const max = Math.max(...module.payload.series.map((item) => item.value));
  const points = buildSparklinePoints(module.payload.series);
  const areaPath = buildAreaPath(module.payload.series);

  return (
    <ModuleFrame compact={compact}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <ModuleEyebrow>{module.payload.metric}</ModuleEyebrow>
          <ModuleTitle>{module.title}</ModuleTitle>
        </div>
        <ModuleMetaBadge>{module.payload.time_range}</ModuleMetaBadge>
      </div>
      <div className="mt-5 rounded-[calc(var(--radius)+1px)] border border-border bg-[var(--panel-muted)] p-4">
        <div className="flex items-end justify-between text-xs text-muted-foreground">
          <span>{max.toFixed(1)}</span>
          <span>{module.payload.unit}</span>
        </div>
        <div className="mt-3 h-44 w-full">
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full overflow-visible">
            <defs>
              <linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="var(--primary-solid)" stopOpacity="0.3" />
                <stop offset="95%" stopColor="var(--primary-solid)" stopOpacity="0.04" />
              </linearGradient>
            </defs>
            <path d={areaPath} fill={`url(#${gradientId})`} />
            <polyline
              fill="none"
              stroke="var(--primary-solid)"
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeLinecap="round"
              points={points}
            />
          </svg>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
          <span>{module.payload.series[0]?.label}</span>
          <span>{module.payload.series[module.payload.series.length - 1]?.label}</span>
        </div>
        <div className="mt-4 grid gap-2 sm:grid-cols-4">
          {module.payload.series.map((item) => (
            <MetricCell key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
        <div className="mt-3 text-xs text-muted-foreground">Range: {min.toFixed(1)} to {max.toFixed(1)}</div>
      </div>
    </ModuleFrame>
  );
}

function MetricTable({ module, compact }: { module: Extract<VisualModule, { type: "metric_table" }>; compact?: boolean }) {
  return (
    <ModuleFrame compact={compact} className="overflow-hidden">
      <div className="flex items-start justify-between gap-4">
        <div>
          <ModuleEyebrow>{module.payload.metric}</ModuleEyebrow>
          <ModuleTitle>{module.title}</ModuleTitle>
        </div>
        {module.payload.sort ? <ModuleMetaBadge>{module.payload.sort}</ModuleMetaBadge> : null}
      </div>
      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[30rem] text-left text-sm">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              {module.payload.columns.map((column) => (
                <th key={column.key} className="pb-3 pr-4 font-medium">
                  {column.label}
                </th>
              ))}
              <th className="pb-3 font-medium">Type</th>
            </tr>
          </thead>
          <tbody>
            {module.payload.rows.map((row, index) => (
              <tr key={`${index}-${row.values[module.payload.columns[0]?.key ?? "row"]}`} className="border-b border-[hsl(var(--border)/0.62)]">
                {module.payload.columns.map((column) => (
                  <td key={column.key} className="py-3 pr-4 text-foreground">
                    {String(row.values[column.key] ?? "n/a")}
                  </td>
                ))}
                <td className="py-3 text-muted-foreground">{row.raw ? "raw" : row.derived ? "derived" : "mixed"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ModuleFrame>
  );
}

function EvidencePanel({ module, compact }: { module: Extract<VisualModule, { type: "evidence_panel" }>; compact?: boolean }) {
  return (
    <ModuleFrame compact={compact}>
      <ModuleEyebrow>{module.payload.review_status}</ModuleEyebrow>
      <ModuleTitle>{module.title}</ModuleTitle>
      <dl className="mt-5 space-y-4">
        <DefinitionItem label="Confidence" value={module.payload.confidence} />
        <DefinitionItem label="Missingness" value={module.payload.missingness} />
        <DefinitionItem label="Provenance" value={module.payload.provenance} />
      </dl>
      <ul className="mt-5 space-y-2">
        {module.payload.sources.map((source) => (
          <li key={`${source.kind}-${source.reference}`}>
            <SourceItem label={source.label} reference={source.reference} />
          </li>
        ))}
      </ul>
    </ModuleFrame>
  );
}

function FormulaCard({ module, compact }: { module: Extract<VisualModule, { type: "formula_explanation_card" }>; compact?: boolean }) {
  return (
    <ModuleFrame compact={compact}>
      <ModuleEyebrow>{module.payload.formula_id}</ModuleEyebrow>
      <ModuleTitle>{module.title}</ModuleTitle>
      <ModuleCodeBlock value={module.payload.expression} />
      <ModuleBodyCopy>{module.payload.interpretation}</ModuleBodyCopy>
      <AssumptionList assumptions={module.payload.assumptions} />
    </ModuleFrame>
  );
}

function VideoPanel({ module, compact }: { module: Extract<VisualModule, { type: "video_panel" }>; compact?: boolean }) {
  return (
    <ModuleFrame compact={compact}>
      <ModuleEyebrow>{module.payload.asset_id}</ModuleEyebrow>
      <ModuleTitle>{module.payload.title}</ModuleTitle>
      <div className="mt-5 flex aspect-video items-center justify-center rounded-[calc(var(--radius)+1px)] border border-dashed border-[var(--panel-border-strong)] bg-[var(--panel-muted)] text-sm text-muted-foreground">
        Video panel placeholder
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <ModuleMetaBadge>{module.payload.timestamp_range}</ModuleMetaBadge>
        {module.payload.related_metrics.map((metric) => (
          <ModuleMetaBadge key={metric}>{metric}</ModuleMetaBadge>
        ))}
      </div>
    </ModuleFrame>
  );
}

function ComparisonCards({ module, compact }: { module: Extract<VisualModule, { type: "comparison_cards" }>; compact?: boolean }) {
  return (
    <ModuleFrame compact={compact}>
      <ModuleEyebrow>{module.title}</ModuleEyebrow>
      <ModuleTitle>{module.payload.title}</ModuleTitle>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {module.payload.items.map((item) => (
          <ComparisonItem key={item.label} label={item.label} value={item.value} delta={item.delta} />
        ))}
      </div>
    </ModuleFrame>
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
