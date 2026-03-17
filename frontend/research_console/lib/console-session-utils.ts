export type ConsoleSession = {
  session_id: string;
  title: string;
  status: string;
  created_at: string;
  dog_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type SessionListResponse = {
  sessions?: ConsoleSession[];
};

export type SessionCreateResponse = {
  session_id?: string;
};

export function getSessionTimestamp(session: ConsoleSession): number {
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

export function sortSessionsByMostRecent(sessions: ConsoleSession[]): ConsoleSession[] {
  return [...sessions].sort((left, right) => getSessionTimestamp(right) - getSessionTimestamp(left));
}

export function formatSessionTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown time";
  }

  return date.toLocaleString("en-AU", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function getSessionDescriptor(session: ConsoleSession | null): string {
  if (!session) {
    return "Waiting for session context";
  }

  if (session.dog_id) {
    return `Dog ${session.dog_id}`;
  }

  return session.status || "Active research session";
}

export function getSessionStatusTone(isBusy: boolean, threadId: string): string {
  if (isBusy) {
    return "Syncing";
  }

  if (!threadId) {
    return "Initializing";
  }

  return "Ready";
}
