import { NextResponse } from "next/server";

import { getHoundForwardApiBase } from "@/lib/hound-forward-api";

export async function GET() {
  const response = await fetch(`${getHoundForwardApiBase()}/sessions`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    return NextResponse.json({ error: "Failed to load console sessions." }, { status: response.status });
  }

  const payload = (await response.json()) as { sessions?: unknown[] };
  return NextResponse.json({ sessions: payload.sessions ?? [] });
}

export async function POST() {
  const timestamp = new Date().toLocaleString("en-AU", {
    dateStyle: "medium",
    timeStyle: "short",
  });
  const response = await fetch(`${getHoundForwardApiBase()}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: `Research Console ${timestamp}`,
      metadata: { source: "research-console" },
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    return NextResponse.json({ error: "Failed to create agent session." }, { status: response.status });
  }

  const payload = (await response.json()) as { session_id?: string };
  if (!payload.session_id) {
    return NextResponse.json({ error: "Agent session response was missing session_id." }, { status: 502 });
  }

  return NextResponse.json({ session_id: payload.session_id });
}
