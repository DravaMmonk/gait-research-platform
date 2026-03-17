import { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/ui/panel";

export function ViewLibrarySectionHeader({
  eyebrow,
  title,
  summary,
  action,
}: {
  eyebrow: string;
  title: string;
  summary: string;
  action?: ReactNode;
}) {
  return (
    <Panel tone="default" padding="roomy" className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div className="min-w-0 flex-1">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{eyebrow}</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-foreground">{title}</h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">{summary}</p>
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </Panel>
  );
}

export function ViewLibraryTagList({ tags }: { tags: string[] }) {
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag) => (
        <Badge key={tag} variant="outline" className="rounded-full px-2.5 py-1 text-[0.68rem] tracking-[0.12em]">
          {tag}
        </Badge>
      ))}
    </div>
  );
}

export function ViewLibraryMetaList({ items }: { items: Array<{ label: string; value: ReactNode }> }) {
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {items.map((item) => (
        <Panel key={item.label} tone="subtle" padding="compact" className="min-w-0">
          <dt className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted-foreground">{item.label}</dt>
          <dd className="mt-2 min-w-0 overflow-hidden text-sm font-medium leading-6 text-foreground">{item.value}</dd>
        </Panel>
      ))}
    </dl>
  );
}

export function ViewLibraryCodeBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <Panel tone="default" padding="roomy" className="min-w-0">
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{title}</p>
      <pre className="mt-4 overflow-x-auto rounded-[calc(var(--radius)+1px)] border border-slate-800 bg-slate-950 p-4 font-mono text-[0.84rem] text-slate-100">
        {JSON.stringify(value, null, 2)}
      </pre>
    </Panel>
  );
}
