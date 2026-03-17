import { NextResponse } from "next/server";

import { getHoundForwardApiBase } from "@/lib/hound-forward-api";

export async function POST() {
  const response = await fetch(`${getHoundForwardApiBase()}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: "Research Console Session",
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
