import { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/ui/panel";

export function Shell({
  children,
  description,
  eyebrow,
  title,
}: {
  children: ReactNode;
  description?: string;
  eyebrow: string;
  title: string;
}) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.08),transparent_24rem),linear-gradient(180deg,hsl(40_22%_98%)_0%,hsl(42_22%_95%)_48%,hsl(40_14%_92%)_100%)] px-4 py-6 sm:px-6">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-[1400px] flex-col gap-5">
        <Panel tone="elevated" padding="roomy" className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{eyebrow}</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-foreground">{title}</h1>
            {description ? <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p> : null}
          </div>
          <Badge variant="outline" className="w-fit">
            Internal route
          </Badge>
        </Panel>

        <div className="min-h-0 flex-1">{children}</div>
      </section>
    </main>
  );
}
