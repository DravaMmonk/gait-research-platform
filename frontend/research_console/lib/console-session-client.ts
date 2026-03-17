import { SessionCreateResponse, SessionListResponse } from "@/lib/console-session-utils";

const SESSION_ENDPOINT = "/api/console/session";

export async function fetchConsoleSessions(): Promise<SessionListResponse> {
  const response = await fetch(SESSION_ENDPOINT, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load sessions.");
  }

  return (await response.json()) as SessionListResponse;
}

export async function createConsoleSession(): Promise<SessionCreateResponse> {
  const response = await fetch(SESSION_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    throw new Error("Unable to create a session.");
  }

  return (await response.json()) as SessionCreateResponse;
}
