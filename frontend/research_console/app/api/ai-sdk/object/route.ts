import { streamObject } from "ai";
import { NextResponse } from "next/server";

import { defaultGaitInsightInput, gaitInsightInputSchema, gaitInsightSchema } from "@/lib/ai-sdk-playground";
import { buildMockInsight, createMockJsonTextResponse, getAiSdkModel, getAiSdkRuntimeStatus } from "@/lib/ai-sdk-server";

export const maxDuration = 30;

export async function POST(request: Request) {
  const body = (await request.json()) as Partial<typeof defaultGaitInsightInput>;
  const parsed = gaitInsightInputSchema.safeParse({
    ...defaultGaitInsightInput,
    ...body,
  });

  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid structured object request." }, { status: 400 });
  }

  const input = parsed.data;
  const runtime = getAiSdkRuntimeStatus();
  const seedObject = buildMockInsight(input);
  const model = getAiSdkModel();

  if (!model) {
    return createMockJsonTextResponse(seedObject, undefined, {
      characterMode: true,
      chunkDelayMs: 10,
    });
  }

  const result = streamObject({
    model,
    schema: gaitInsightSchema,
    prompt: [
      "Generate a compact structured gait analysis payload.",
      `Subject: ${input.subject}`,
      `Concern: ${input.concern}`,
      `Video label: ${input.videoLabel}`,
      `Runtime mode: ${runtime.mode}`,
      `Use these deterministic metrics exactly: ${JSON.stringify(seedObject.metrics)}`,
      `Use this summary direction: ${seedObject.summary}`,
      "Return short findings and next actions. Do not provide diagnosis.",
    ].join("\n"),
  });

  return result.toTextStreamResponse();
}
