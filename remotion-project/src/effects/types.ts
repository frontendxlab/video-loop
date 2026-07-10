import { z } from "zod";

/** Each effect layer type and its config. */
export const GlitchConfigSchema = z.object({
  type: z.literal("glitch"),
  intensity: z.number().min(0).max(1).default(0.5),
  scanlineCount: z.number().int().positive().default(12),
  offsetMax: z.number().min(0).default(8),
});

export const VintageConfigSchema = z.object({
  type: z.literal("vintage"),
  grainIntensity: z.number().min(0).max(1).default(0.15),
  sepiaMix: z.number().min(0).max(1).default(0.6),
  vignetteStrength: z.number().min(0).max(1).default(0.3),
});

export const MagnifierConfigSchema = z.object({
  type: z.literal("magnifier"),
  radius: z.number().positive().default(80),
  zoom: z.number().min(1).max(4).default(2),
  centerX: z.number().min(0).max(1).default(0.5),
  centerY: z.number().min(0).max(1).default(0.5),
});

export const EffectLayerSchema = z.discriminatedUnion("type", [
  GlitchConfigSchema,
  VintageConfigSchema,
  MagnifierConfigSchema,
]);

export type GlitchConfig = z.infer<typeof GlitchConfigSchema>;
export type VintageConfig = z.infer<typeof VintageConfigSchema>;
export type MagnifierConfig = z.infer<typeof MagnifierConfigSchema>;
export type EffectLayer = z.infer<typeof EffectLayerSchema>;
export type EffectType = EffectLayer["type"];
