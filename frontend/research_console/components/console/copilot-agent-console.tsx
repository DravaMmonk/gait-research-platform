"use client";

import Image from "next/image";
import { useEffect, useEffectEvent, useMemo, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { CopilotKitInspector, useCopilotKit } from "@copilotkitnext/react";

const starterPrompts = [
  { title: "Summarize", message: "Summarize this session." },
  { title: "Videos", message: "List the uploaded video assets in the current session." },
  { title: "Evidence", message: "Explain the evidence." },
];

const ACTIVE_SESSION_STORAGE_KEY = "hound-forward-active-session-id";
const ARCHIVED_SESSION_STORAGE_KEY = "hound-forward-archived-session-ids";

type ConsoleSession = {
  session_id: string;
  title: string;
  status: string;
  created_at: string;
  dog_id?: string | null;
  metadata?: Record<string, unknown>;
};

type SessionListResponse = {
  sessions?: ConsoleSession[];
};

type SessionCreateResponse = {
  session_id?: string;
};

function ExplicitCopilotInspector() {
  const { copilotkit } = useCopilotKit();

  return <CopilotKitInspector core={copilotkit ?? undefined} />;
}

function getSessionTimestamp(session: ConsoleSession): number {
  const metadata = session.metadata;
  const rawUpdatedAt =
    typeof metadata?.updated_at === "string"
      ? metadata.updated_at
      : typeof metadata?.updatedAt === "string"
        ? metadata.updatedAt
        : session.created_at;
  const timestamp = new Date(rawUpdatedAt).getTime();
  if (!Number.isNaN(timestamp)) {
    return timestamp;
  }

  const fallback = new Date(session.created_at).getTime();
  return Number.isNaN(fallback) ? 0 : fallback;
}

function sortSessionsByMostRecent(sessions: ConsoleSession[]): ConsoleSession[] {
  return [...sessions].sort((left, right) => getSessionTimestamp(right) - getSessionTimestamp(left));
}

function formatSessionTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown time";
  }
  return date.toLocaleString("en-AU", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function CopilotAgentConsole() {
  const [sessions, setSessions] = useState<ConsoleSession[]>([]);
  const [threadId, setThreadId] = useState("");
  const [status, setStatus] = useState("Loading sessions");
  const [isBusy, setIsBusy] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [archivedSessionIds, setArchivedSessionIds] = useState<string[]>([]);
  const [isArchivedExpanded, setIsArchivedExpanded] = useState(false);

  function setActiveSession(sessionId: string, availableSessions: ConsoleSession[] = sessions) {
    setThreadId(sessionId);
    if (sessionId) {
      window.localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, sessionId);
      const selected = availableSessions.find((session) => session.session_id === sessionId);
      setStatus(selected ? `Current session: ${selected.title}` : `Current session: ${sessionId.slice(0, 8)}`);
      return;
    }
    window.localStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
    setStatus("No active session");
  }

  async function refreshSessions(preferredSessionId?: string) {
    const response = await fetch("/api/console/session", {
      method: "GET",
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error("Unable to refresh sessions.");
    }
    const payload = (await response.json()) as SessionListResponse;
    const loadedSessions = sortSessionsByMostRecent(payload.sessions ?? []);
    const storedArchivedIds = JSON.parse(window.localStorage.getItem(ARCHIVED_SESSION_STORAGE_KEY) ?? "[]") as unknown[];
    const nextArchivedIds = storedArchivedIds
      .filter((value): value is string => typeof value === "string")
      .filter((sessionId) => loadedSessions.some((session) => session.session_id === sessionId));
    setSessions(loadedSessions);
    setArchivedSessionIds(nextArchivedIds);
    window.localStorage.setItem(ARCHIVED_SESSION_STORAGE_KEY, JSON.stringify(nextArchivedIds));
    const visibleSessions = loadedSessions.filter((session) => !nextArchivedIds.includes(session.session_id));
    const nextSessionId =
      preferredSessionId && visibleSessions.some((session) => session.session_id === preferredSessionId)
        ? preferredSessionId
        : visibleSessions[0]?.session_id ?? "";
    setActiveSession(nextSessionId, loadedSessions);
    return loadedSessions;
  }

  async function createSession(options?: { replaceStatus?: string }) {
    setIsBusy(true);
    try {
      const response = await fetch("/api/console/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        throw new Error("Unable to create a session.");
      }

      const payload = (await response.json()) as SessionCreateResponse;
      if (!payload.session_id) {
        throw new Error("Session creation response was incomplete.");
      }

      await refreshSessions(payload.session_id);
      if (options?.replaceStatus) {
        setStatus(options.replaceStatus);
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to create a session.");
    } finally {
      setIsBusy(false);
    }
  }

  useEffect(() => {
    window.localStorage.removeItem("cpk:inspector:hidden");
    window.localStorage.removeItem("cpk:inspector:state");
  }, []);

  const initializeSessions = useEffectEvent(async () => {
    try {
      const response = await fetch("/api/console/session", {
        method: "GET",
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error("Unable to load sessions.");
      }

      const payload = (await response.json()) as SessionListResponse;
      const loadedSessions = sortSessionsByMostRecent(payload.sessions ?? []);
      const archivedIds = JSON.parse(window.localStorage.getItem(ARCHIVED_SESSION_STORAGE_KEY) ?? "[]") as unknown[];
      const normalizedArchivedIds = archivedIds.filter((value): value is string => typeof value === "string");
      setArchivedSessionIds(normalizedArchivedIds);
      if (loadedSessions.length === 0) {
        await createSession({ replaceStatus: "Created a new session" });
        return;
      }

      setSessions(loadedSessions);
      const persisted = window.localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY);
      const visibleSessions = loadedSessions.filter((session) => !normalizedArchivedIds.includes(session.session_id));
      const selected =
        visibleSessions.find((session) => session.session_id === persisted)?.session_id ?? visibleSessions[0]?.session_id ?? "";
      setActiveSession(selected, loadedSessions);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to load sessions.");
    }
  });

  useEffect(() => {
    void initializeSessions();
  }, []);

  function archiveSession(sessionId: string) {
    const nextArchivedIds = archivedSessionIds.includes(sessionId) ? archivedSessionIds : [...archivedSessionIds, sessionId];
    setArchivedSessionIds(nextArchivedIds);
    window.localStorage.setItem(ARCHIVED_SESSION_STORAGE_KEY, JSON.stringify(nextArchivedIds));

    const nextVisibleSessions = sessions.filter((session) => !nextArchivedIds.includes(session.session_id));
    if (threadId === sessionId) {
      setActiveSession(nextVisibleSessions[0]?.session_id ?? "", sessions);
    }

    const archivedSession = sessions.find((session) => session.session_id === sessionId);
    setStatus(archivedSession ? `Archived ${archivedSession.title}` : "Archived session");
  }

  function restoreSession(sessionId: string) {
    const nextArchivedIds = archivedSessionIds.filter((value) => value !== sessionId);
    setArchivedSessionIds(nextArchivedIds);
    window.localStorage.setItem(ARCHIVED_SESSION_STORAGE_KEY, JSON.stringify(nextArchivedIds));

    const restoredSession = sessions.find((session) => session.session_id === sessionId);
    setStatus(restoredSession ? `Restored ${restoredSession.title}` : "Restored session");
  }

  const activeSession = useMemo(
    () => sessions.find((session) => session.session_id === threadId) ?? null,
    [sessions, threadId],
  );
  const archivedIdSet = useMemo(() => new Set(archivedSessionIds), [archivedSessionIds]);
  const visibleSessions = useMemo(
    () => sessions.filter((session) => !archivedIdSet.has(session.session_id)),
    [archivedIdSet, sessions],
  );
  const archivedSessions = useMemo(
    () => sessions.filter((session) => archivedIdSet.has(session.session_id)),
    [archivedIdSet, sessions],
  );

  return (
    <main className="hound-shell">
      <section className={`hound-frame${isSidebarCollapsed ? " hound-frame-sidebar-collapsed" : ""}`}>
        <aside
          className={`hound-session-sidebar${isSidebarCollapsed ? " hound-session-sidebar-collapsed" : ""}`}
          aria-label="Research sessions"
        >
          {!isSidebarCollapsed ? (
            <>
              <div className="hound-sidebar-header">
                <button type="button" className="hound-sidebar-brand-button" aria-label="Hound Forward">
                  <div className="hound-sidebar-brand-logo-frame">
                    <Image
                      src="/houndforward_logo.png"
                      alt="Hound Forward"
                      className="hound-sidebar-brand-logo"
                      width={56}
                      height={32}
                      priority
                    />
                  </div>
                  <div className="hound-sidebar-brand-copy">
                    <span className="hound-sidebar-brand-title">Hound Forward</span>
                    <span className="hound-sidebar-brand-subtitle">Research Console</span>
                  </div>
                </button>
                <button
                  type="button"
                  className="hound-session-sidebar-toggle"
                  onClick={() => setIsSidebarCollapsed((value) => !value)}
                  aria-expanded={!isSidebarCollapsed}
                  aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                  title="Toggle Sidebar"
                >
                  <svg
                    className="hound-session-toggle-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
                    <path d="M9 4.5V19.5" />
                    <path d="M18 9L15 12L18 15" />
                  </svg>
                  <span className="sr-only">Collapse Sidebar</span>
                </button>
              </div>
              <div className="hound-sidebar-content">
                <section className="hound-sidebar-group" aria-labelledby="research-actions-label">
                  <div className="hound-sidebar-group-label" id="research-actions-label">
                    Research
                  </div>
                  <div className="hound-sidebar-menu" role="list">
                    <div className="hound-sidebar-menu-item" role="listitem">
                      <button
                        className="hound-sidebar-menu-button hound-sidebar-menu-button-primary"
                        onClick={() => void createSession()}
                        disabled={isBusy}
                      >
                        <svg
                          className="hound-sidebar-menu-icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          aria-hidden="true"
                        >
                          <path d="M12 5V19" />
                          <path d="M5 12H19" />
                        </svg>
                        <span>New Session</span>
                      </button>
                    </div>
                  </div>
                </section>

                <section className="hound-sidebar-group hound-sidebar-group-fill" aria-labelledby="sessions-label">
                  <div className="hound-sidebar-group-label" id="sessions-label">
                    Sessions
                  </div>
                  <div className="hound-sidebar-menu hound-sidebar-session-menu" role="list">
                    {visibleSessions.map((session) => {
                      const isActive = session.session_id === threadId;
                      return (
                        <div key={session.session_id} className="hound-sidebar-menu-item" role="listitem">
                          <article
                            className={`hound-sidebar-session-row${isActive ? " hound-sidebar-session-row-active" : ""}`}
                          >
                            <button
                              type="button"
                              className={`hound-sidebar-menu-button hound-sidebar-session-button${
                                isActive ? " hound-sidebar-menu-button-active" : ""
                              }`}
                              onClick={() => setActiveSession(session.session_id)}
                              title={session.title}
                            >
                              <svg
                                className="hound-sidebar-menu-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="1.8"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                aria-hidden="true"
                              >
                                <path d="M7 8H17" />
                                <path d="M7 12H15" />
                                <path d="M7 16H13" />
                                <rect x="4" y="5" width="16" height="14" rx="2.5" />
                              </svg>
                              <span className="hound-sidebar-session-copy">
                                <span className="hound-sidebar-session-title">{session.title}</span>
                                <span className="hound-sidebar-session-meta">{formatSessionTimestamp(session.created_at)}</span>
                              </span>
                            </button>
                            <button
                              className="hound-session-delete"
                              onClick={(event) => {
                                event.stopPropagation();
                                archiveSession(session.session_id);
                              }}
                              disabled={isBusy}
                              aria-label={`Archive ${session.title}`}
                              title="Archive session"
                            >
                              <svg
                                className="hound-sidebar-delete-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="1.8"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                aria-hidden="true"
                              >
                                <path d="M3.5 7.5H20.5V18C20.5 19.1 19.6 20 18.5 20H5.5C4.4 20 3.5 19.1 3.5 18V7.5Z" />
                                <path d="M8 7.5V5.8C8 4.81 8.81 4 9.8 4H14.2C15.19 4 16 4.81 16 5.8V7.5" />
                                <path d="M8 11.5H16" />
                              </svg>
                            </button>
                          </article>
                        </div>
                      );
                    })}
                  </div>
                </section>
              </div>
              <div className="hound-sidebar-footer">
                <button
                  type="button"
                  className={`hound-sidebar-footer-toggle${isArchivedExpanded ? " hound-sidebar-footer-toggle-open" : ""}`}
                  onClick={() => setIsArchivedExpanded((value) => !value)}
                  aria-expanded={isArchivedExpanded}
                  aria-controls="archived-sessions-panel"
                >
                  <span className="hound-sidebar-footer-toggle-copy">
                    <span className="hound-sidebar-footer-label">Archived Sessions</span>
                    <span className="hound-sidebar-footer-count">{archivedSessions.length}</span>
                  </span>
                  <svg
                    className="hound-sidebar-footer-chevron"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d={isArchivedExpanded ? "M18 15L12 9L6 15" : "M6 9L12 15L18 9"} />
                  </svg>
                </button>
                {isArchivedExpanded ? (
                  <div className="hound-sidebar-archived-panel" id="archived-sessions-panel" role="list">
                    {archivedSessions.length > 0 ? (
                      archivedSessions.map((session) => (
                        <div key={session.session_id} className="hound-sidebar-menu-item" role="listitem">
                          <article className="hound-sidebar-session-row">
                            <button
                              type="button"
                              className="hound-sidebar-menu-button hound-sidebar-session-button"
                              onClick={() => restoreSession(session.session_id)}
                              title={`Restore ${session.title}`}
                            >
                              <svg
                                className="hound-sidebar-menu-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="1.8"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                aria-hidden="true"
                              >
                                <path d="M8 7H4V11" />
                                <path d="M4 7L9 12" />
                                <path d="M20 17A7 7 0 0 1 8.7 20.7L6 18" />
                                <path d="M16 4A7 7 0 0 1 19.3 15.3" />
                              </svg>
                              <span className="hound-sidebar-session-copy">
                                <span className="hound-sidebar-session-title">{session.title}</span>
                                <span className="hound-sidebar-session-meta">{formatSessionTimestamp(session.created_at)}</span>
                              </span>
                            </button>
                          </article>
                        </div>
                      ))
                    ) : (
                      <p className="hound-sidebar-archived-empty">No archived sessions.</p>
                    )}
                  </div>
                ) : null}
              </div>
            </>
          ) : (
            <>
              <div className="hound-sidebar-collapsed-header">
                <button
                  type="button"
                  className="hound-session-sidebar-toggle"
                  onClick={() => setIsSidebarCollapsed((value) => !value)}
                  aria-expanded={!isSidebarCollapsed}
                  aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                  title="Toggle Sidebar"
                >
                  <svg
                    className="hound-session-toggle-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <rect x="3.5" y="4.5" width="17" height="15" rx="2.5" />
                    <path d="M9 4.5V19.5" />
                    <path d="M15 9L18 12L15 15" />
                  </svg>
                  <span className="sr-only">Expand Sidebar</span>
                </button>
              </div>
              <div className="hound-session-rail" role="list">
                <button
                  type="button"
                  className="hound-session-rail-item"
                  onClick={() => void createSession()}
                  disabled={isBusy}
                  aria-label="New session"
                  title="New session"
                >
                  <svg
                    className="hound-sidebar-menu-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M12 5V19" />
                    <path d="M5 12H19" />
                  </svg>
                </button>
                {visibleSessions.map((session) => {
                  const isActive = session.session_id === threadId;
                  const railLabel = session.title.trim().charAt(0).toUpperCase() || "S";

                  return (
                    <button
                      key={session.session_id}
                      type="button"
                      className={`hound-session-rail-item${isActive ? " hound-session-rail-item-active" : ""}`}
                      onClick={() => setActiveSession(session.session_id)}
                      aria-label={session.title}
                      title={session.title}
                    >
                      {railLabel}
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </aside>

        <section className="hound-chat-card">
          {threadId ? (
            <CopilotKit key={threadId} runtimeUrl="/api/copilotkit" threadId={threadId}>
              <>
                <ExplicitCopilotInspector />
                <CopilotChat
                  className="hound-chat"
                  labels={{
                    title: activeSession ? activeSession.title : "Agent",
                    initial: "Ask a question about the current session.",
                  }}
                  suggestions={starterPrompts}
                />
              </>
            </CopilotKit>
          ) : (
            <section className="hound-loading-card">
              <p className="agent-kicker">Agent</p>
              <h2 className="agent-panel-title">Loading console</h2>
            </section>
          )}
        </section>
      </section>
    </main>
  );
}
