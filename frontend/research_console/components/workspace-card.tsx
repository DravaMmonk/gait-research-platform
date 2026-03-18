import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/ui/panel";

export type WorkspaceCardItem = {
  id: string;
  eyebrow: string;
  title: string;
  summary: string;
  status: string;
  metrics: Array<{ label: string; value: string }>;
};

export function WorkspaceCardList({ cards }: { cards: WorkspaceCardItem[] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {cards.map((card) => (
        <Panel key={card.id} tone="default" padding="roomy" className="space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{card.eyebrow}</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-foreground">{card.title}</h2>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{card.summary}</p>
            </div>
            <Badge variant="muted">{card.status}</Badge>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {card.metrics.map((metric) => (
              <Panel key={`${card.id}-${metric.label}`} tone="subtle" padding="compact" className="min-w-0">
                <p className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted-foreground">{metric.label}</p>
                <p className="mt-2 text-sm font-semibold text-foreground">{metric.value}</p>
              </Panel>
            ))}
          </div>
        </Panel>
      ))}
    </div>
  );
}
