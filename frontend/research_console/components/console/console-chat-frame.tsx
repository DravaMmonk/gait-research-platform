"use client";

import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/ui/panel";
import { type ConsoleSession, formatSessionTimestamp } from "@/lib/console-session-utils";
import { CopilotSessionChat } from "./copilot-session-chat";

type ConsoleChatFrameProps = {
  activeSession: ConsoleSession | null;
  sessionDescriptor: string;
  sessionStatusTone: string;
  status: string;
  threadId: string;
};

function ContextItem({ label, value, multiline = false }: { label: string; value: string; multiline?: boolean }) {
  return (
    <div className="grid gap-1 px-5 py-4 first:pl-6 last:pr-6 md:border-r md:border-[hsl(var(--border)/0.66)] md:last:border-r-0">
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
      <p className={multiline ? "text-sm font-semibold leading-6 text-foreground" : "truncate text-sm font-semibold text-foreground"}>{value}</p>
    </div>
  );
}

export function ConsoleChatFrame({
  activeSession,
  sessionDescriptor,
  sessionStatusTone,
  status,
  threadId,
}: ConsoleChatFrameProps) {
  return (
    <section className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-5 px-4 py-4 sm:px-6 sm:py-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">CopilotKit chat</p>
          <h1 className="mt-1 text-[clamp(1.75rem,1.45rem+1vw,2.35rem)] font-bold tracking-[-0.04em] text-foreground">
            {activeSession?.title ?? "Research Console"}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{sessionDescriptor}</p>
        </div>
        <Badge variant="default" className="w-fit rounded-full px-3 py-1 text-[0.68rem] tracking-[0.14em]">
          {sessionStatusTone}
        </Badge>
      </header>

      <Panel tone="elevated" padding="none" className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] overflow-hidden rounded-[1.4rem]">
        <div className="grid border-b border-[hsl(var(--border)/0.68)] bg-[hsl(var(--secondary)/0.44)] md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_1.3fr]">
          <ContextItem label="Session" value={threadId ? `${threadId.slice(0, 8)}...` : "Initializing"} />
          <ContextItem
            label="Created"
            value={activeSession ? formatSessionTimestamp(activeSession.created_at) : "Preparing workspace"}
          />
          <ContextItem label="Status" value={status} multiline />
        </div>

        {threadId ? (
          <div className="min-h-0">
            <CopilotSessionChat threadId={threadId} />
          </div>
        ) : (
          <div className="grid min-h-0 place-items-center px-6 py-16">
            <div className="max-w-md space-y-2 text-left">
              <p className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Loading</p>
              <h2 className="text-2xl font-semibold tracking-[-0.03em] text-foreground">Preparing chat workspace</h2>
              <p className="text-sm leading-6 text-muted-foreground">A session will be selected or created automatically.</p>
            </div>
          </div>
        )}
      </Panel>
    </section>
  );
}
