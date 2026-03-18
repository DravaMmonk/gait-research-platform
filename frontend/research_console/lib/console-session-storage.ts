const ACTIVE_SESSION_STORAGE_KEY = "hound-forward-active-session-id";
const ARCHIVED_SESSION_STORAGE_KEY = "hound-forward-archived-session-ids";

function safeParseStringArray(raw: string | null): string[] {
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as unknown[];
    return parsed.filter((value): value is string => typeof value === "string");
  } catch {
    return [];
  }
}

export function readActiveSessionId(): string {
  return window.localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY) ?? "";
}

export function writeActiveSessionId(sessionId: string) {
  if (sessionId) {
    window.localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, sessionId);
    return;
  }

  window.localStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
}

export function readArchivedSessionIds(): string[] {
  return safeParseStringArray(window.localStorage.getItem(ARCHIVED_SESSION_STORAGE_KEY));
}

export function writeArchivedSessionIds(sessionIds: string[]) {
  window.localStorage.setItem(ARCHIVED_SESSION_STORAGE_KEY, JSON.stringify(sessionIds));
}
