import { z } from "zod";

export const devChatStarterPrompts = [
  "Analyze a short gait clip and explain which metrics matter most.",
  "What tools are available in this AI SDK playground?",
  "Is the playground running in live model mode or mock mode?",
] as const;

export const devCompletionPrompts = [
  "Write a concise operator update for a gait analysis run.",
  "Summarize why streaming matters in an AI-native research console.",
  "Draft a short tooltip for a symmetry score card.",
] as const;

export const gaitInsightInputSchema = z.object({
  subject: z.string().min(1).max(80).default("Scout"),
  concern: z.string().min(1).max(160).default("Possible hind-limb asymmetry after exercise"),
  videoLabel: z.string().min(1).max(120).default("session-video-001"),
});

export type GaitInsightInput = z.infer<typeof gaitInsightInputSchema>;

export const gaitInsightSchema = z.object({
  summary: z.string(),
  subject: z.string(),
  concern: z.string(),
  videoLabel: z.string(),
  metrics: z.object({
    strideLength: z.number(),
    symmetryScore: z.number(),
    cadence: z.number(),
    confidence: z.number(),
  }),
  findings: z.array(z.string()),
  nextActions: z.array(z.string()),
  toolTrace: z.array(
    z.object({
      tool: z.string(),
      status: z.enum(["live", "mock"]),
      detail: z.string(),
    }),
  ),
});

export type GaitInsight = z.infer<typeof gaitInsightSchema>;

export const defaultGaitInsightInput: GaitInsightInput = {
  subject: "Scout",
  concern: "Possible hind-limb asymmetry after exercise",
  videoLabel: "session-video-001",
};
