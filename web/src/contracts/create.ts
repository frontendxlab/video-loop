import { z } from "zod";

export const VoiceEnum = z.enum([
  "alba","alice","bella","carla","diana","elena",
  "fiona","gina","helen","iris","julia","kate",
  "laura","maria","nora","olivia","paula","quinn",
  "rita","sara","tina","ursula","vera","wanda","xena","zara",
]);
export type Voice = z.infer<typeof VoiceEnum>;

export const CreateOptionsSchema = z.object({
  voice: VoiceEnum.default("alba"),
  provider: z.enum(["openai","anthropic","google","deepseek","custom"]).default("openai"),
  model: z.string().default("gpt-4o"),
  maxDuration: z.number().positive().default(180),
  fps: z.number().positive().default(30),
});
export type CreateOptions = z.infer<typeof CreateOptionsSchema>;

export const CreateJobRequestSchema = z.object({
  prompt: z.string().min(10, "Prompt must be at least 10 characters"),
  options: CreateOptionsSchema,
});
export type CreateJobRequest = z.infer<typeof CreateJobRequestSchema>;

export const SceneSuggestionSchema = z.object({
  kind: z.string(), title: z.string(), description: z.string(), reasoning: z.string(),
});
export type SceneSuggestion = z.infer<typeof SceneSuggestionSchema>;

export const GrillResultSchema = z.object({
  refinedPrompt: z.string(),
  suggestedScenes: z.array(SceneSuggestionSchema),
  missingDetails: z.array(z.string()),
  confidence: z.number().min(0).max(1),
});
export type GrillResult = z.infer<typeof GrillResultSchema>;

export const DEFAULT_OPTIONS: CreateOptions = {
  voice: "alba", provider: "openai", model: "gpt-4o", maxDuration: 180, fps: 30,
};

export const CREATE_STAGES = [
  { id: "grill", label: "Grill prompt" },
  { id: "plan", label: "Plan scenes" },
  { id: "audio", label: "Generate audio" },
  { id: "render", label: "Render video" },
  { id: "review", label: "Review quality" },
] as const;
