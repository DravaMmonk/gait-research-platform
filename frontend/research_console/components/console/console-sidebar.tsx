"use client";

import Image from "next/image";
import { ArchiveRestore, FolderArchive, PanelLeftClose, PanelLeftOpen, Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { formatSessionTimestamp, type ConsoleSession } from "@/lib/console-session-utils";
import { cn } from "@/lib/utils";

type ConsoleSidebarProps = {
  activeSessionId: string;
  archivedSessions: ConsoleSession[];
  isArchivedExpanded: boolean;
  isBusy: boolean;
  isCollapsed: boolean;
  visibleSessions: ConsoleSession[];
  onArchiveSession: (sessionId: string) => void;
  onCreateSession: () => void;
  onRestoreSession: (sessionId: string) => void;
  onSelectSession: (sessionId: string) => void;
  onToggleArchive: () => void;
  onToggleCollapsed: () => void;
};

function SessionAvatar({ session, muted = false }: { session: ConsoleSession; muted?: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex h-10 w-10 items-center justify-center rounded-[0.8rem] border text-sm font-semibold",
        muted
          ? "border-[hsl(var(--border)/0.66)] bg-muted text-muted-foreground"
          : "border-[hsl(var(--primary)/0.14)] bg-secondary text-foreground",
      )}
    >
      {session.title.trim().charAt(0).toUpperCase() || "S"}
    </span>
  );
}

function SidebarBrand() {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="inline-flex h-11 w-14 items-center justify-center rounded-[0.95rem]">
        <Image
          src="/logo.png"
          alt="Hound Forward"
          className="h-auto w-14 object-contain"
          width={56}
          height={32}
          priority
        />
      </span>
      <div className="min-w-0">
        <p className="truncate text-base font-bold tracking-[-0.03em] text-foreground">Hound Forward</p>
        <p className="truncate text-xs font-medium text-muted-foreground">Research Console</p>
      </div>
    </div>
  );
}

function ExpandedSessionList({
  activeSessionId,
  sessions,
  isBusy,
  onArchiveSession,
  onSelectSession,
}: {
  activeSessionId: string;
  sessions: ConsoleSession[];
  isBusy: boolean;
  onArchiveSession: (sessionId: string) => void;
  onSelectSession: (sessionId: string) => void;
}) {
  return (
    <ScrollArea className="min-h-0 flex-1">
      <div className="grid gap-3 pr-3">
        {sessions.map((session) => {
          const isActive = session.session_id === activeSessionId;

          return (
            <Panel
              key={session.session_id}
              tone={isActive ? "elevated" : "subtle"}
              padding="none"
              className={cn(
                "grid grid-cols-[minmax(0,1fr)_auto] items-center overflow-hidden transition-colors",
                isActive && "border-[hsl(var(--primary)/0.3)] bg-[linear-gradient(180deg,hsl(var(--card))_0%,hsl(var(--primary)/0.08)_100%)]",
              )}
            >
              <button
                type="button"
                className="flex min-w-0 items-center gap-3 px-4 py-3 text-left"
                onClick={() => onSelectSession(session.session_id)}
                title={session.title}
              >
                <SessionAvatar session={session} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-semibold text-foreground">{session.title}</span>
                  <span className="block text-xs text-muted-foreground">{formatSessionTimestamp(session.created_at)}</span>
                </span>
              </button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="mr-2 h-9 w-9 rounded-full text-muted-foreground"
                onClick={() => onArchiveSession(session.session_id)}
                disabled={isBusy}
                aria-label={`Archive ${session.title}`}
                title="Archive session"
              >
                <FolderArchive />
              </Button>
            </Panel>
          );
        })}
      </div>
    </ScrollArea>
  );
}

function CollapsedSessionRail({
  activeSessionId,
  sessions,
  isBusy,
  onCreateSession,
  onSelectSession,
}: {
  activeSessionId: string;
  sessions: ConsoleSession[];
  isBusy: boolean;
  onCreateSession: () => void;
  onSelectSession: (sessionId: string) => void;
}) {
  return (
    <div className="flex h-full flex-col items-center gap-3 px-2 py-4">
      <Button type="button" variant="outline" size="icon" className="rounded-[0.9rem]" onClick={onCreateSession} disabled={isBusy}>
        <Plus />
      </Button>
      <Separator className="w-9 bg-[hsl(var(--border)/0.66)]" />
      <ScrollArea className="min-h-0 w-full flex-1">
        <div className="grid gap-3 pb-2">
          {sessions.map((session) => {
            const isActive = session.session_id === activeSessionId;

            return (
              <Button
                key={session.session_id}
                type="button"
                variant={isActive ? "secondary" : "outline"}
                size="icon"
                className={cn(
                  "h-12 w-12 rounded-[0.95rem] border-border text-sm font-semibold shadow-none",
                  isActive && "border-[hsl(var(--primary)/0.3)] bg-accent text-accent-foreground",
                )}
                onClick={() => onSelectSession(session.session_id)}
                aria-label={session.title}
                title={session.title}
              >
                {session.title.trim().charAt(0).toUpperCase() || "S"}
              </Button>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}

export function ConsoleSidebar({
  activeSessionId,
  archivedSessions,
  isArchivedExpanded,
  isBusy,
  isCollapsed,
  visibleSessions,
  onArchiveSession,
  onCreateSession,
  onRestoreSession,
  onSelectSession,
  onToggleArchive,
  onToggleCollapsed,
}: ConsoleSidebarProps) {
  return (
    <aside
      className={cn(
        "h-full min-h-0 overflow-hidden border-r border-[hsl(var(--border)/0.74)] bg-[linear-gradient(180deg,hsl(42_24%_97%)_0%,hsl(40_18%_95%)_100%)]",
        isCollapsed ? "grid grid-rows-[auto_minmax(0,1fr)]" : "grid grid-rows-[auto_auto_auto_minmax(0,1fr)_auto]",
      )}
      aria-label="Research sessions"
    >
      <div className={cn("flex items-center border-b border-[hsl(var(--border)/0.72)]", isCollapsed ? "justify-center px-3 py-4" : "justify-between gap-3 px-5 py-4")}>
        {!isCollapsed ? <SidebarBrand /> : null}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="rounded-[0.8rem]"
          onClick={onToggleCollapsed}
          aria-expanded={!isCollapsed}
          aria-label={isCollapsed ? "Expand session sidebar" : "Collapse session sidebar"}
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
        </Button>
      </div>

      {isCollapsed ? (
        <CollapsedSessionRail
          activeSessionId={activeSessionId}
          sessions={visibleSessions}
          isBusy={isBusy}
          onCreateSession={onCreateSession}
          onSelectSession={onSelectSession}
        />
      ) : (
        <>
          <div className="px-5 py-5">
            <Button type="button" className="w-full justify-center rounded-[0.95rem]" onClick={onCreateSession} disabled={isBusy}>
              <Plus />
              <span>New session</span>
            </Button>
          </div>

          <div className="grid min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-4 px-5 pb-5">
            <div className="flex items-center justify-between gap-3 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              <span>Active sessions</span>
              <Badge variant="muted" className="rounded-full px-2 py-0.5 text-[0.68rem] tracking-[0.12em]">
                {visibleSessions.length}
              </Badge>
            </div>
            <ExpandedSessionList
              activeSessionId={activeSessionId}
              sessions={visibleSessions}
              isBusy={isBusy}
              onArchiveSession={onArchiveSession}
              onSelectSession={onSelectSession}
            />
          </div>

          <div className="mt-auto border-t border-[hsl(var(--border)/0.68)] px-5 py-4">
            <Button
              type="button"
              variant="outline"
              className="w-full justify-between rounded-[0.95rem] px-4"
              onClick={onToggleArchive}
              aria-expanded={isArchivedExpanded}
              aria-controls="archived-sessions-panel"
            >
              <span>Archived sessions</span>
              <Badge variant="muted" className="rounded-full px-2 py-0.5 text-[0.68rem] tracking-[0.12em]">
                {archivedSessions.length}
              </Badge>
            </Button>
            {isArchivedExpanded ? (
              <ScrollArea className="mt-4 h-48" id="archived-sessions-panel">
                <div className="grid gap-3 pr-3">
                  {archivedSessions.length ? (
                    archivedSessions.map((session) => (
                      <Panel key={session.session_id} tone="muted" padding="none" className="overflow-hidden">
                        <button
                          type="button"
                          className="flex w-full items-center gap-3 px-4 py-3 text-left"
                          onClick={() => onRestoreSession(session.session_id)}
                          title={`Restore ${session.title}`}
                        >
                          <SessionAvatar session={session} muted />
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-sm font-semibold text-foreground">{session.title}</span>
                            <span className="block text-xs text-muted-foreground">{formatSessionTimestamp(session.created_at)}</span>
                          </span>
                          <ArchiveRestore className="h-4 w-4 text-muted-foreground" />
                        </button>
                      </Panel>
                    ))
                  ) : (
                    <p className="pr-2 pt-1 text-sm text-muted-foreground">No archived sessions.</p>
                  )}
                </div>
              </ScrollArea>
            ) : null}
          </div>
        </>
      )}
    </aside>
  );
}
