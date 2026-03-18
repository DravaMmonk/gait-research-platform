"use client";

import { useState } from "react";

import { ConsoleChatFrame } from "@/components/console/console-chat-frame";
import { ConsoleSidebar } from "@/components/console/console-sidebar";
import { useConsoleSessions } from "@/hooks/use-console-sessions";

export function CopilotAgentConsole() {
  const [isArchivedExpanded, setIsArchivedExpanded] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const {
    activeSession,
    archivedSessions,
    createSession,
    isBusy,
    threadId,
    visibleSessions,
    archiveSession,
    restoreSession,
    selectSession,
  } = useConsoleSessions();

  return (
    <main className="relative h-dvh min-h-dvh max-h-dvh overflow-hidden bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.08),transparent_24rem),linear-gradient(180deg,hsl(40_22%_98%)_0%,hsl(42_22%_95%)_48%,hsl(40_14%_92%)_100%)]">
      <section
        className={
          isSidebarCollapsed
            ? "grid h-dvh min-h-dvh max-h-dvh grid-cols-[4.75rem_minmax(0,1fr)] overflow-hidden"
            : "grid h-dvh min-h-dvh max-h-dvh grid-cols-[22rem_minmax(0,1fr)] overflow-hidden"
        }
      >
        <ConsoleSidebar
          activeSessionId={threadId}
          archivedSessions={archivedSessions}
          isArchivedExpanded={isArchivedExpanded}
          isBusy={isBusy}
          isCollapsed={isSidebarCollapsed}
          visibleSessions={visibleSessions}
          onArchiveSession={archiveSession}
          onCreateSession={() => void createSession()}
          onRestoreSession={restoreSession}
          onSelectSession={selectSession}
          onToggleArchive={() => setIsArchivedExpanded((value) => !value)}
          onToggleCollapsed={() => setIsSidebarCollapsed((value) => !value)}
        />
        <ConsoleChatFrame
          activeSession={activeSession}
          threadId={threadId}
        />
      </section>
    </main>
  );
}
