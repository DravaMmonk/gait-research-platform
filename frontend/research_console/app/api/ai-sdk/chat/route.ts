import { convertToModelMessages, smoothStream, stepCountIs, streamText, tool, type UIMessage } from "ai";
import { NextResponse } from "next/server";
import { z } from "zod";

import { buildMockInsight, createMockChatResponse, getAiSdkModel, getAiSdkRuntimeStatus } from "@/lib/ai-sdk-server";

export const maxDuration = 30;

const analyzeGaitMetricsSchema = z.object({
  subject: z.string().min(1).default("Scout"),
  concern: z.string().min(1).default("Review the latest gait clip"),
  videoLabel: z.string().min(1).default("main-interface-demo"),
});

export async function POST(request: Request) {
  const { messages } = (await request.json()) as { messages?: UIMessage[] };

  if (!messages?.length) {
    return NextResponse.json({ error: "Missing chat messages." }, { status: 400 });
  }

  const model = getAiSdkModel();
  if (!model) {
    return createMockChatResponse(messages);
  }

  const modelMessages = await convertToModelMessages(messages);

  const result = streamText({
    model,
    system: [
      "You are an engineering-facing AI SDK workbench assistant inside a gait research console.",
      "Use tools whenever the user asks about metrics, video analysis, runtime status, or environment setup.",
      "Keep answers concise and practical.",
      "Do not provide diagnosis or treatment recommendations.",
    ].join(" "),
    messages: modelMessages,
    tools: {
      analyze_gait_metrics: tool({
        description: "Generate a deterministic gait metric bundle for the requested subject or clip.",
        inputSchema: analyzeGaitMetricsSchema,
        execute: async (input) => buildMockInsight(input),
      }),
      get_runtime_status: tool({
        description: "Return the active AI SDK runtime mode and model configuration.",
        inputSchema: z.object({}),
        execute: async () => getAiSdkRuntimeStatus(),
      }),
    },
    stopWhen: stepCountIs(5),
    experimental_transform: smoothStream({
      delayInMs: 10,
      chunking: /[\s\S]/,
    }),
  });

  return result.toUIMessageStreamResponse();
}
