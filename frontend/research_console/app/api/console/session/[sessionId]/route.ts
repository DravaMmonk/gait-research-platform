import { NextResponse } from "next/server";

import { getHoundForwardApiBase } from "@/lib/hound-forward-api";

type RouteContext = {
  params: Promise<{
    sessionId: string;
  }>;
};

export async function DELETE(_request: Request, context: RouteContext) {
  const { sessionId } = await context.params;
  const response = await fetch(`${getHoundForwardApiBase()}/sessions/${sessionId}`, {
    method: "DELETE",
    cache: "no-store",
  });

  if (!response.ok) {
    return NextResponse.json({ error: "Failed to delete console session." }, { status: response.status });
  }

  const payload = (await response.json()) as { deleted?: boolean; session_id?: string };
  return NextResponse.json({
    deleted: payload.deleted ?? false,
    session_id: payload.session_id ?? sessionId,
  });
}
