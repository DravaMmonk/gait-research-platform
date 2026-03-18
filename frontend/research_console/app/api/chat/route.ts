import { NextResponse } from "next/server";
import { createUIMessageStream, createUIMessageStreamResponse, generateId } from "ai";

import { getHoundForwardApiBase } from "@/lib/hound-forward-api";
import type { ChatResponsePayload, ConsoleUIMessage } from "@/lib/console-types";

export const maxDuration = 30;

function getLatestUserMessage(messages: ConsoleUIMessage[]): string {
  const latest = [...messages].reverse().find((message) => message.role === "user");

  if (!latest) {
    return "";
  }

  return latest.parts
    .filter((part): part is Extract<ConsoleUIMessage["parts"][number], { type: "text" }> => part.type === "text")
    .map((part) => part.text)
    .join("\n")
    .trim();
}

export async function POST(request: Request) {
  const {
    messages,
    threadId,
  } = (await request.json()) as {
    messages?: ConsoleUIMessage[];
    threadId?: string;
  };

  if (!threadId) {
    return NextResponse.json({ error: "Missing threadId." }, { status: 400 });
  }

  const userMessage = getLatestUserMessage(messages ?? []);
  if (!userMessage) {
    return NextResponse.json({ error: "Missing user message." }, { status: 400 });
  }

  try {
    const response = await fetch(`${getHoundForwardApiBase()}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: threadId,
        message: userMessage,
        context: {},
      }),
      cache: "no-store",
      signal: request.signal,
    });

    if (!response.ok) {
      return NextResponse.json({ error: `Hound Forward responded with ${response.status}.` }, { status: response.status });
    }

    const payload = (await response.json()) as ChatResponsePayload;
    const stream = createUIMessageStream<ConsoleUIMessage>({
      originalMessages: messages ?? [],
      generateId,
      execute: ({ writer }) => {
        const textId = generateId();

        for (const [index, progress] of (payload.progress_messages ?? []).entries()) {
          writer.write({
            type: "data-progress",
            id: `${generateId()}-${index}`,
            data: { message: progress },
          });
        }

        writer.write({
          type: "data-result",
          id: generateId(),
          data: payload,
        });
        writer.write({
          type: "text-start",
          id: textId,
        });
        writer.write({
          type: "text-delta",
          id: textId,
          delta: payload.message,
        });
        writer.write({
          type: "text-end",
          id: textId,
        });
      },
    });

    return createUIMessageStreamResponse({ stream });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "The assistant is currently unavailable." },
      { status: 500 },
    );
  }
}
