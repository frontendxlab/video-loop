import { z } from "zod";

/* ─── Provider ─── */

export const PROVIDER_IDS = [
  "openai",
  "anthropic",
  "google",
  "groq",
  "9router",
  "custom",
] as const;

export type ProviderId = (typeof PROVIDER_IDS)[number];

export const ProviderConfigSchema = z.object({
  provider: z.enum(PROVIDER_IDS),
  label: z.string().min(1),
  apiKey: z.string().default(""),
  baseUrl: z.string().url().or(z.literal("")).default(""),
  defaultModel: z.string().min(1),
  models: z.array(
    z.object({
      id: z.string().min(1),
      label: z.string().min(1),
      maxTokens: z.number().int().positive().default(4096),
    }),
  ),
});

export type ProviderConfig = z.infer<typeof ProviderConfigSchema>;

/* ─── Queue ─── */

export const QueueSettingsSchema = z.object({
  maxConcurrency: z.number().int().min(1).max(32).default(4),
  maxQueueSize: z.number().int().min(1).max(500).default(100),
});

export type QueueSettings = z.infer<typeof QueueSettingsSchema>;

/* ─── Retry ─── */

export const RetrySettingsSchema = z.object({
  maxRetries: z.number().int().min(0).max(10).default(3),
  retryDelayMs: z.number().int().min(0).max(60_000).default(2000),
  exponentialBackoff: z.boolean().default(true),
});

export type RetrySettings = z.infer<typeof RetrySettingsSchema>;

/* ─── Review ─── */

export const ReviewThresholdsSchema = z.object({
  l0MinScore: z.number().min(0).max(1).default(0.9),
  l1MinScore: z.number().min(0).max(1).default(0.85),
  coherenceGateEnabled: z.boolean().default(true),
});

export type ReviewThresholds = z.infer<typeof ReviewThresholdsSchema>;

/* ─── Root settings ─── */

export const SettingsSchema = z.object({
  activeProvider: z.enum(PROVIDER_IDS),
  activeModel: z.string().min(1),
  providers: z.array(ProviderConfigSchema).default([]),
  queue: QueueSettingsSchema,
  retry: RetrySettingsSchema,
  review: ReviewThresholdsSchema,
});

export type Settings = z.infer<typeof SettingsSchema>;

/* ─── Defaults ─── */

export const DEFAULT_SETTINGS: Settings = {
  activeProvider: "9router",
  activeModel: "ocg/deepseek-v4-flash",
  providers: [
    {
      provider: "openai",
      label: "OpenAI",
      apiKey: "",
      baseUrl: "",
      defaultModel: "gpt-4o",
      models: [
        { id: "gpt-4o", label: "GPT-4o", maxTokens: 16_384 },
        { id: "gpt-4o-mini", label: "GPT-4o Mini", maxTokens: 16_384 },
        { id: "o1", label: "o1", maxTokens: 32_768 },
      ],
    },
    {
      provider: "anthropic",
      label: "Anthropic",
      apiKey: "",
      baseUrl: "",
      defaultModel: "claude-sonnet-4-20250514",
      models: [
        { id: "claude-sonnet-4-20250514", label: "Claude Sonnet 4", maxTokens: 8192 },
        { id: "claude-opus-4-20250514", label: "Claude Opus 4", maxTokens: 8192 },
      ],
    },
    {
      provider: "google",
      label: "Google",
      apiKey: "",
      baseUrl: "",
      defaultModel: "gemini-2.0-flash",
      models: [
        { id: "gemini-2.0-flash", label: "Gemini 2.0 Flash", maxTokens: 8192 },
        { id: "gemini-2.0-pro", label: "Gemini 2.0 Pro", maxTokens: 8192 },
      ],
    },
    {
      provider: "groq",
      label: "Groq",
      apiKey: "",
      baseUrl: "",
      defaultModel: "llama-3.3-70b",
      models: [
        { id: "llama-3.3-70b", label: "Llama 3.3 70B", maxTokens: 8192 },
        { id: "mixtral-8x7b", label: "Mixtral 8×7B", maxTokens: 8192 },
      ],
    },
    {
      provider: "9router",
      label: "9router",
      apiKey: "",
      baseUrl: "",
      defaultModel: "ocg/deepseek-v4-flash",
      models: [
        { id: "ocg/deepseek-v4-flash", label: "DeepSeek V4 Flash", maxTokens: 32_768 },
        { id: "ocg/deepseek-v4-flash:free", label: "DeepSeek V4 Flash Free", maxTokens: 8_192 },
      ],
    },
    {
      provider: "custom",
      label: "Custom",
      apiKey: "",
      baseUrl: "",
      defaultModel: "custom-model",
      models: [{ id: "custom-model", label: "Custom Model", maxTokens: 4096 }],
    },
  ],
  queue: { maxConcurrency: 4, maxQueueSize: 100 },
  retry: { maxRetries: 3, retryDelayMs: 2000, exponentialBackoff: true },
  review: { l0MinScore: 0.9, l1MinScore: 0.85, coherenceGateEnabled: true },
};

/* ─── Per-run override ─── */

export const RunOverrideSchema = z.object({
  provider: z.string().optional(),
  model: z.string().optional(),
  temperature: z.number().min(0).max(2).default(0.7),
  maxTokens: z.number().int().positive().default(4096),
});

export type RunOverride = z.infer<typeof RunOverrideSchema>;
