import { smoothStream, streamText } from "ai";
import { NextResponse } from "next/server";

import { createMockTextResponse, getAiSdkModel } from "@/lib/ai-sdk-server";

export const maxDuration = 30;

export async function POST(request: Request) {
  const { prompt } = (await request.json()) as { prompt?: string };

  if (!prompt?.trim()) {
    return NextResponse.json({ error: "Missing prompt." }, { status: 400 });
  }

  const model = getAiSdkModel();
  if (!model) {
    return createMockTextResponse(
      `Operator update: ${prompt.trim()} Streaming stays enabled so researchers can see partial progress before the full write-up is complete.`,
      undefined,
      { characterMode: true, chunkDelayMs: 14 },
    );
  }

  const result = streamText({
    model,
    system:
      "You write concise product-facing copy for a gait research interface. Keep responses practical, short, and safe. Do not provide diagnosis.",
    prompt,
    experimental_transform: smoothStream({
      delayInMs: 12,
      chunking: /[\s\S]/,
    }),
  });

  return result.toTextStreamResponse();
}
