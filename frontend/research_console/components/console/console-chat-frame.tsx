"use client";

import { Panel } from "@/components/ui/panel";
import { type ConsoleSession } from "@/lib/console-session-utils";
import { SessionChat } from "./session-chat";

type ConsoleChatFrameProps = {
  activeSession: ConsoleSession | null;
  threadId: string;
};

export function ConsoleChatFrame({
  activeSession,
  threadId,
}: ConsoleChatFrameProps) {
  return (
    <section className="grid h-full min-h-0 overflow-hidden px-4 py-4 sm:px-6 sm:py-6">
      <Panel tone="elevated" padding="none" className="grid h-full min-h-0 overflow-hidden rounded-[1.4rem]">
        {threadId ? (
          <div className="min-h-0 overflow-hidden">
            <SessionChat threadId={threadId} />
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
