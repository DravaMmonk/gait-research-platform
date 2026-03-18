"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { createConsoleSession, fetchConsoleSessions } from "@/lib/console-session-client";
import { readActiveSessionId, readArchivedSessionIds, resetCopilotInspectorState, writeActiveSessionId, writeArchivedSessionIds } from "@/lib/console-session-storage";
import {
  ConsoleSession,
  sortSessionsByMostRecent,
} from "@/lib/console-session-utils";

function normalizeArchivedSessionIds(sessions: ConsoleSession[], archivedSessionIds: string[]) {
  return archivedSessionIds.filter((sessionId) => sessions.some((session) => session.session_id === sessionId));
}

export function useConsoleSessions() {
  const [sessions, setSessions] = useState<ConsoleSession[]>([]);
  const [threadId, setThreadId] = useState("");
  const [status, setStatus] = useState("Loading sessions");
  const [isBusy, setIsBusy] = useState(false);
  const [archivedSessionIds, setArchivedSessionIds] = useState<string[]>([]);
  const sessionsRef = useRef<ConsoleSession[]>([]);
  const createSessionRef = useRef<(replaceStatus?: string) => Promise<void>>(async () => undefined);

  useEffect(() => {
    sessionsRef.current = sessions;
  }, [sessions]);

  function setActiveSession(nextSessionId: string, availableSessions: ConsoleSession[] = sessionsRef.current) {
    setThreadId(nextSessionId);
    writeActiveSessionId(nextSessionId);

    if (!nextSessionId) {
      setStatus("No active session");
      return;
    }

    const selected = availableSessions.find((session) => session.session_id === nextSessionId);
    setStatus(selected ? `Current session: ${selected.title}` : `Current session: ${nextSessionId.slice(0, 8)}`);
  }

  async function refreshSessions(preferredSessionId?: string) {
    const payload = await fetchConsoleSessions();
    const loadedSessions = sortSessionsByMostRecent(payload.sessions ?? []);
    const nextArchivedSessionIds = normalizeArchivedSessionIds(loadedSessions, readArchivedSessionIds());
    const visibleSessions = loadedSessions.filter((session) => !nextArchivedSessionIds.includes(session.session_id));
    const nextSessionId =
      preferredSessionId && visibleSessions.some((session) => session.session_id === preferredSessionId)
        ? preferredSessionId
        : visibleSessions[0]?.session_id ?? "";

    setSessions(loadedSessions);
    setArchivedSessionIds(nextArchivedSessionIds);
    writeArchivedSessionIds(nextArchivedSessionIds);
    setActiveSession(nextSessionId, loadedSessions);
    return loadedSessions;
  }

  async function handleCreateSession(replaceStatus?: string) {
    setIsBusy(true);
    try {
      const payload = await createConsoleSession();
      if (!payload.session_id) {
        throw new Error("Session creation response was incomplete.");
      }

      await refreshSessions(payload.session_id);
      if (replaceStatus) {
        setStatus(replaceStatus);
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to create a session.");
    } finally {
      setIsBusy(false);
    }
  }

  useEffect(() => {
    createSessionRef.current = handleCreateSession;
  });

  function archiveSession(sessionId: string) {
    const nextArchivedSessionIds = archivedSessionIds.includes(sessionId)
      ? archivedSessionIds
      : [...archivedSessionIds, sessionId];
    const nextVisibleSessions = sessions.filter((session) => !nextArchivedSessionIds.includes(session.session_id));
    const archivedSession = sessions.find((session) => session.session_id === sessionId);

    setArchivedSessionIds(nextArchivedSessionIds);
    writeArchivedSessionIds(nextArchivedSessionIds);

    if (threadId === sessionId) {
      setActiveSession(nextVisibleSessions[0]?.session_id ?? "", sessions);
    }

    setStatus(archivedSession ? `Archived ${archivedSession.title}` : "Archived session");
  }

  function restoreSession(sessionId: string) {
    const nextArchivedSessionIds = archivedSessionIds.filter((value) => value !== sessionId);
    const restoredSession = sessions.find((session) => session.session_id === sessionId);

    setArchivedSessionIds(nextArchivedSessionIds);
    writeArchivedSessionIds(nextArchivedSessionIds);
    setStatus(restoredSession ? `Restored ${restoredSession.title}` : "Restored session");
  }

  useEffect(() => {
    resetCopilotInspectorState();
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function initializeSessions() {
      try {
        const payload = await fetchConsoleSessions();
        if (cancelled) {
          return;
        }

        const loadedSessions = sortSessionsByMostRecent(payload.sessions ?? []);
        const nextArchivedSessionIds = normalizeArchivedSessionIds(loadedSessions, readArchivedSessionIds());

        setArchivedSessionIds(nextArchivedSessionIds);
        writeArchivedSessionIds(nextArchivedSessionIds);

        if (!loadedSessions.length) {
          await createSessionRef.current("Created a new session");
          return;
        }

        const visibleSessions = loadedSessions.filter((session) => !nextArchivedSessionIds.includes(session.session_id));
        const persistedSessionId = readActiveSessionId();
        const selectedSessionId =
          visibleSessions.find((session) => session.session_id === persistedSessionId)?.session_id ?? visibleSessions[0]?.session_id ?? "";

        setSessions(loadedSessions);
        setActiveSession(selectedSessionId, loadedSessions);
      } catch (error) {
        if (!cancelled) {
          setStatus(error instanceof Error ? error.message : "Unable to load sessions.");
        }
      }
    }

    void initializeSessions();

    return () => {
      cancelled = true;
    };
  }, []);

  const archivedIdSet = useMemo(() => new Set(archivedSessionIds), [archivedSessionIds]);
  const visibleSessions = useMemo(
    () => sessions.filter((session) => !archivedIdSet.has(session.session_id)),
    [archivedIdSet, sessions],
  );
  const archivedSessions = useMemo(
    () => sessions.filter((session) => archivedIdSet.has(session.session_id)),
    [archivedIdSet, sessions],
  );
  const activeSession = useMemo(
    () => sessions.find((session) => session.session_id === threadId) ?? null,
    [sessions, threadId],
  );

  return {
    activeSession,
    archivedSessions,
    isBusy,
    status,
    threadId,
    visibleSessions,
    archiveSession,
    createSession: handleCreateSession,
    refreshSessions,
    restoreSession,
    selectSession: setActiveSession,
  };
}
