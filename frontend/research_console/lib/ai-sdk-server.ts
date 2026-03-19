import "server-only";

import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import type { UIMessage } from "ai";
import { createUIMessageStream, createUIMessageStreamResponse, generateId } from "ai";
import { createVertex } from "@ai-sdk/google-vertex";
import { openai } from "@ai-sdk/openai";

import type { GaitInsight, GaitInsightInput } from "@/lib/ai-sdk-playground";

const DEFAULT_MODEL = "gpt-4o-mini";
const DEFAULT_TEXT_CHUNK_DELAY_MS = 18;
const DEFAULT_JSON_CHUNK_DELAY_MS = 22;

export type AiSdkRuntimeStatus = {
  configured: boolean;
  mode: "live" | "mock";
  provider: "google-vertex" | "openai" | "mock";
  model: string;
  reason: string;
};

type ResolvedRuntimeConfig =
  | {
      provider: "google-vertex";
      model: string;
      project: string;
      location: string;
      apiKey?: string;
    }
  | {
      provider: "openai";
      model: string;
    }
  | null;

let cachedRepoEnv: Record<string, string> | null = null;

function hashToUnit(value: string): number {
  const digest = createHash("sha256").update(value).digest("hex").slice(0, 8);
  const normalized = Number.parseInt(digest, 16) / 0xffffffff;
  return Number.isFinite(normalized) ? normalized : 0.5;
}

function parseEnvFile(content: string): Record<string, string> {
  const entries: Record<string, string> = {};

  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }

    const index = line.indexOf("=");
    if (index <= 0) {
      continue;
    }

    const key = line.slice(0, index).trim();
    let value = line.slice(index + 1).trim();

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    entries[key] = value;
  }

  return entries;
}

function getRepoEnv(): Record<string, string> {
  if (cachedRepoEnv) {
    return cachedRepoEnv;
  }

  const cwd = process.cwd();
  const candidateRoots = [
    cwd,
    path.resolve(cwd, ".."),
    path.resolve(cwd, "..", ".."),
  ];
  const collected: Record<string, string> = {};

  for (const root of candidateRoots) {
    for (const file of [path.join(root, ".env"), path.join(root, ".env.local")]) {
      if (!existsSync(file)) {
        continue;
      }

      Object.assign(collected, parseEnvFile(readFileSync(file, "utf8")));
    }
  }

  cachedRepoEnv = collected;
  return collected;
}

function getEnvValue(keys: string[]): string | undefined {
  const repoEnv = getRepoEnv();

  for (const key of keys) {
    const runtimeValue = process.env[key];
    if (runtimeValue) {
      return runtimeValue;
    }

    const repoValue = repoEnv[key];
    if (repoValue) {
      return repoValue;
    }
  }

  return undefined;
}

function resolveRuntimeConfig(): ResolvedRuntimeConfig {
  const provider = getEnvValue(["HF_LLM_PROVIDER"]);

  if (provider === "vertex_ai" || provider === "google_vertex") {
    const project = getEnvValue([
      "GOOGLE_VERTEX_PROJECT",
      "HF_GCP_PROJECT_ID",
      "GOOGLE_CLOUD_PROJECT",
      "GCLOUD_PROJECT",
      "GCP_PROJECT_ID",
    ]);
    const location =
      getEnvValue([
        "GOOGLE_VERTEX_LOCATION",
        "HF_GCP_LOCATION",
        "GOOGLE_CLOUD_LOCATION",
        "GOOGLE_CLOUD_REGION",
        "GCP_REGION",
      ]) ?? "global";
    const model = getEnvValue(["HF_LLM_MODEL"]) ?? "gemini-2.5-flash";
    const apiKey = getEnvValue(["GOOGLE_VERTEX_API_KEY"]);

    if (project || apiKey) {
      return {
        provider: "google-vertex",
        model,
        project: project ?? "",
        location,
        apiKey,
      };
    }
  }

  if (getEnvValue(["OPENAI_API_KEY"])) {
    return {
      provider: "openai",
      model: getEnvValue(["OPENAI_MODEL"]) ?? DEFAULT_MODEL,
    };
  }

  return null;
}

export function getAiSdkRuntimeStatus(): AiSdkRuntimeStatus {
  const config = resolveRuntimeConfig();

  if (!config) {
    return {
      configured: false,
      mode: "mock",
      provider: "mock",
      model: "mock-gait-runtime",
      reason: "No live AI provider is configured for the frontend workbench. It falls back to deterministic mock streaming.",
    };
  }

  if (config.provider === "google-vertex") {
    return {
      configured: true,
      mode: "live",
      provider: "google-vertex",
      model: config.model,
      reason: `Vertex AI is configured from ${config.project ? "project/location settings" : "API key settings"}. Authentication still depends on ADC or GOOGLE_VERTEX_API_KEY being available at runtime.`,
    };
  }

  return {
    configured: true,
    mode: "live",
    provider: "openai",
    model: config.model,
    reason: "OpenAI provider is configured. Tool calling and object generation are running against a live model.",
  };
}

export function getAiSdkModel() {
  const config = resolveRuntimeConfig();

  if (!config) {
    return null;
  }

  if (config.provider === "google-vertex") {
    const provider = createVertex({
      project: config.project || undefined,
      location: config.location,
      apiKey: config.apiKey,
    });
    return provider.languageModel(config.model);
  }

  return openai(config.model);
}

function round(value: number, digits = 3) {
  return Number(value.toFixed(digits));
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function splitIntoCharacters(value: string): string[] {
  return Array.from(value);
}

export function buildMockInsight(input: GaitInsightInput): GaitInsight {
  const seed = `${input.subject}:${input.concern}:${input.videoLabel}`;
  const strideLength = round(0.68 + hashToUnit(`${seed}:stride`) * 0.34, 2);
  const symmetryScore = round(0.72 + hashToUnit(`${seed}:symmetry`) * 0.24, 2);
  const cadence = round(1.7 + hashToUnit(`${seed}:cadence`) * 0.9, 2);
  const confidence = round(0.81 + hashToUnit(`${seed}:confidence`) * 0.16, 2);
  const dominantSide = hashToUnit(`${seed}:side`) > 0.5 ? "right" : "left";
  const runtime = getAiSdkRuntimeStatus();

  return {
    summary:
      symmetryScore < 0.85
        ? `${input.subject} shows a mild ${dominantSide}-leaning asymmetry pattern that warrants follow-up review.`
        : `${input.subject} shows a mostly stable gait pattern with only light asymmetry drift.`,
    subject: input.subject,
    concern: input.concern,
    videoLabel: input.videoLabel,
    metrics: {
      strideLength,
      symmetryScore,
      cadence,
      confidence,
    },
    findings: [
      `Stride length normalized to ${strideLength} m across the sampled clip.`,
      `Symmetry score settled at ${symmetryScore}, which is ${symmetryScore < 0.85 ? "below" : "within"} the preferred review band.`,
      `Cadence stabilized near ${cadence} Hz with ${confidence} confidence in the derived trace.`,
    ],
    nextActions: [
      "Compare this clip against the latest baseline run before escalating interpretation.",
      "Review frame windows around stance-to-swing transition for timing drift.",
      "Use the same camera angle on the next capture to keep metric deltas comparable.",
    ],
    toolTrace: [
      {
        tool: "analyze_gait_metrics",
        status: runtime.mode,
        detail: `Generated deterministic metric bundle for ${input.videoLabel}.`,
      },
    ],
  };
}

export function createMockTextResponse(
  text: string,
  init?: ResponseInit,
  options?: { chunkDelayMs?: number; characterMode?: boolean; chunkSize?: number },
): Response {
  const encoder = new TextEncoder();
  const chunkSize = options?.chunkSize ?? 28;
  const chunkDelayMs = options?.chunkDelayMs ?? DEFAULT_TEXT_CHUNK_DELAY_MS;
  const chunks = options?.characterMode ? splitIntoCharacters(text) : text.match(new RegExp(`.{1,${chunkSize}}(\\s|$)|\\S+`, "g")) ?? [text];

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      for (const [index, chunk] of chunks.entries()) {
        if (index > 0) {
          await sleep(chunkDelayMs);
        }
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    status: init?.status ?? 200,
    statusText: init?.statusText,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      ...Object.fromEntries(new Headers(init?.headers).entries()),
    },
  });
}

export function createMockJsonTextResponse(
  value: unknown,
  init?: ResponseInit,
  options?: { chunkDelayMs?: number; characterMode?: boolean; chunkSize?: number },
): Response {
  const encoder = new TextEncoder();
  const chunkSize = options?.chunkSize ?? 34;
  const chunkDelayMs = options?.chunkDelayMs ?? DEFAULT_JSON_CHUNK_DELAY_MS;
  const json = JSON.stringify(value, null, 2);
  const chunks = options?.characterMode ? splitIntoCharacters(json) : json.match(new RegExp(`.{1,${chunkSize}}`, "gs")) ?? [json];

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      for (const [index, chunk] of chunks.entries()) {
        if (index > 0) {
          await sleep(chunkDelayMs);
        }
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    status: init?.status ?? 200,
    statusText: init?.statusText,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      ...Object.fromEntries(new Headers(init?.headers).entries()),
    },
  });
}

function getLatestUserText(messages: UIMessage[]): string {
  const latest = [...messages].reverse().find((message) => message.role === "user");
  if (!latest) {
    return "Explain the AI SDK workbench.";
  }

  return latest.parts
    .filter((part): part is Extract<(typeof latest.parts)[number], { type: "text" }> => part.type === "text")
    .map((part) => part.text)
    .join("\n")
    .trim();
}

export function createMockChatResponse(messages: UIMessage[]) {
  const runtime = getAiSdkRuntimeStatus();
  const userText = getLatestUserText(messages);
  const mockInsight = buildMockInsight({
    subject: "Scout",
    concern: userText,
    videoLabel: "main-interface-demo",
  });

  const answer = [
    `Running in ${runtime.mode} mode with ${runtime.model}.`,
    `Tool simulation analyzed ${mockInsight.videoLabel} and produced stride length ${mockInsight.metrics.strideLength} m, symmetry ${mockInsight.metrics.symmetryScore}, cadence ${mockInsight.metrics.cadence} Hz, and confidence ${mockInsight.metrics.confidence}.`,
    mockInsight.summary,
  ].join(" ");

  const stream = createUIMessageStream<UIMessage>({
    originalMessages: messages,
    generateId,
    execute: async ({ writer }) => {
      const textId = generateId();
      const intro = "Mock streaming is active because no provider key is configured. ";
      const chunks = splitIntoCharacters(intro + answer);

      writer.write({ type: "text-start", id: textId });
      for (const [index, chunk] of chunks.entries()) {
        if (index > 0) {
          await sleep(DEFAULT_TEXT_CHUNK_DELAY_MS);
        }
        writer.write({ type: "text-delta", id: textId, delta: chunk });
      }
      writer.write({ type: "text-end", id: textId });
    },
  });

  return createUIMessageStreamResponse({ stream });
}
