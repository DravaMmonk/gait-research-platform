"use client";

import { defaultConsoleResponse } from "@/lib/console-fixtures";
import { ConsoleAgentRequest, ConsoleAgentResponse } from "@/lib/console-types";

const apiBase = process.env.NEXT_PUBLIC_HOUND_FORWARD_API_URL;

export async function requestConsoleResponse(payload: ConsoleAgentRequest): Promise<ConsoleAgentResponse> {
  if (!apiBase) {
    return buildFallbackResponse(payload);
  }

  try {
    const response = await fetch(`${apiBase}/agent/console/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      return buildFallbackResponse(payload);
    }
    return (await response.json()) as ConsoleAgentResponse;
  } catch {
    return buildFallbackResponse(payload);
  }
}

function buildFallbackResponse(payload: ConsoleAgentRequest): ConsoleAgentResponse {
  return {
    ...defaultConsoleResponse,
    thread: [
      {
        role: "user",
        content: payload.message,
        created_at: new Date().toISOString(),
      },
      ...defaultConsoleResponse.thread.filter((item) => item.role === "assistant"),
    ],
  };
}
