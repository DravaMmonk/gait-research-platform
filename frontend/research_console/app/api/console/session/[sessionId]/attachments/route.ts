import { NextRequest, NextResponse } from "next/server";

import { getHoundForwardApiBase } from "@/lib/hound-forward-api";

type RouteContext = {
  params: Promise<{
    sessionId: string;
  }>;
};

export async function POST(request: NextRequest, context: RouteContext) {
  const { sessionId } = await context.params;
  const formData = await request.formData();

  const response = await fetch(`${getHoundForwardApiBase()}/sessions/${sessionId}/attachments`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    return NextResponse.json(
      { error: payload?.detail || "Failed to upload session attachment." },
      { status: response.status },
    );
  }

  return NextResponse.json(await response.json());
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { sessionId } = await context.params;

  const response = await fetch(`${getHoundForwardApiBase()}/sessions/${sessionId}/attachments`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    return NextResponse.json(
      { error: payload?.detail || "Failed to load session attachments." },
      { status: response.status },
    );
  }

  return NextResponse.json(await response.json());
}
