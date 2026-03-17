"use client";

import { useEffect, useMemo, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

const starterPrompts = [
  { title: "Summarize", message: "Summarize this session." },
  { title: "Videos", message: "List the uploaded video assets in the current session." },
  { title: "Evidence", message: "Explain the evidence." },
];

const ACTIVE_SESSION_STORAGE_KEY = "hound-forward-active-session-id";

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

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const response = await fetch("/api/console/session", {
          method: "GET",
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error("Unable to load sessions.");
        }

        const payload = (await response.json()) as SessionListResponse;
        if (cancelled) {
          return;
        }

        const loadedSessions = payload.sessions ?? [];
        if (loadedSessions.length === 0) {
          await createSession({ replaceStatus: "Created a new session" });
          return;
        }

        setSessions(loadedSessions);
        const persisted = window.localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY);
        const selected =
          loadedSessions.find((session) => session.session_id === persisted)?.session_id ?? loadedSessions[0]?.session_id ?? "";
        setActiveSession(selected, loadedSessions);
      } catch (error) {
        if (cancelled) {
          return;
        }
        setStatus(error instanceof Error ? error.message : "Unable to load sessions.");
      }
    }

    initialize();

    return () => {
      cancelled = true;
    };
  }, []);

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
    const loadedSessions = payload.sessions ?? [];
    setSessions(loadedSessions);
    const nextSessionId =
      preferredSessionId && loadedSessions.some((session) => session.session_id === preferredSessionId)
        ? preferredSessionId
        : loadedSessions[0]?.session_id ?? "";
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

  async function deleteSession(sessionId: string) {
    setIsBusy(true);
    try {
      const response = await fetch(`/api/console/session/${sessionId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error("Unable to delete the selected session.");
      }

      const remainingSessions = await refreshSessions(threadId === sessionId ? undefined : threadId);
      if (remainingSessions.length === 0) {
        await createSession({ replaceStatus: "Deleted the session and created a fresh one" });
        return;
      }

      const deletedSession = sessions.find((session) => session.session_id === sessionId);
      setStatus(deletedSession ? `Deleted ${deletedSession.title}` : "Deleted session");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to delete the selected session.");
    } finally {
      setIsBusy(false);
    }
  }

  const activeSession = useMemo(
    () => sessions.find((session) => session.session_id === threadId) ?? null,
    [sessions, threadId],
  );

  return (
    <main className="hound-shell">
      <section className="hound-frame">
        <header className="hound-header">
          <div className="ui-stable-fill">
            <p className="agent-kicker">Hound Forward</p>
            <h1 className="agent-title">Ask the agent</h1>
          </div>
          <div className="agent-status-card" aria-live="polite">
            <span className="agent-status-dot" />
            <p>{status}</p>
          </div>
        </header>

        <section className="hound-console-layout">
          <aside className="hound-session-sidebar">
            <section className="hound-session-sidebar-card">
              <div className="hound-session-sidebar-header">
                <div>
                  <p className="agent-kicker">Sessions</p>
                  <h2 className="agent-panel-title">Manage sessions</h2>
                </div>
                <button className="hound-session-primary-button" onClick={() => void createSession()} disabled={isBusy}>
                  New session
                </button>
              </div>
              <div className="hound-session-list" role="list" aria-label="Research sessions">
                {sessions.map((session) => {
                  const isActive = session.session_id === threadId;
                  return (
                    <article
                      key={session.session_id}
                      className={`hound-session-item${isActive ? " hound-session-item-active" : ""}`}
                    >
                      <button className="hound-session-select" onClick={() => setActiveSession(session.session_id)}>
                        <span className="hound-session-title">{session.title}</span>
                        <span className="hound-session-meta">{formatSessionTimestamp(session.created_at)}</span>
                      </button>
                      <button
                        className="hound-session-delete"
                        onClick={() => void deleteSession(session.session_id)}
                        disabled={isBusy}
                        aria-label={`Delete ${session.title}`}
                      >
                        Delete
                      </button>
                    </article>
                  );
                })}
              </div>
            </section>
          </aside>

          <section className="hound-chat-card">
            {threadId ? (
              <CopilotKit key={threadId} runtimeUrl="/api/copilotkit" threadId={threadId} showDevConsole={false}>
                <CopilotChat
                  className="hound-chat"
                  labels={{
                    title: activeSession ? activeSession.title : "Agent",
                    initial: "Ask a question about the current session.",
                  }}
                  suggestions={starterPrompts}
                />
              </CopilotKit>
            ) : (
              <section className="hound-loading-card">
                <p className="agent-kicker">Agent</p>
                <h2 className="agent-panel-title">Loading console</h2>
              </section>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}
