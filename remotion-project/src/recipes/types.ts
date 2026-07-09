/**
 * Recipe types — showcase-inspired recipe schema for VideoForge.
 *
 * Recipes define reusable video templates: scene graph shape, preferred
 * engine(s), allowed inputs, transition packs, and review rules.
 */

import { z } from "zod";

// ── Engine ──────────────────────────────────────────────────────────

export const EngineSchema = z.enum(["remotion", "manim", "animotion"]);
export type Engine = z.infer<typeof EngineSchema>;

// ── Scene kind ──────────────────────────────────────────────────────

/** Known scene kinds from current compositions + showcase study additions. */
export const SceneKindSchema = z.enum([
  "title",
  "code",
  "diff",
  "bullet",
  "image",
  "comparison",
  "diagram",
  "outro",
  "chart",
  "timeline",
  "map3d",
  "document-highlight",
  "screenflow",
  "hero-intro",
  "overlay-cta",
  "trajectory-timeline",
  "real-estate",
  "3d-ranking",
  "product-promo",
  "audio-reactive",
  "dual-chart",
  "promo",
]);
export type SceneKind = z.infer<typeof SceneKindSchema>;

// ── Recipe ──────────────────────────────────────────────────────────

export const RecipeInputsSchema = z.object({
  /** Free-form prompt used to generate recipe scene graph. */
  prompt: z.string().optional(),
  /** Optional customisation parameters per recipe. */
  params: z.record(z.unknown()).optional(),
});
export type RecipeInputs = z.infer<typeof RecipeInputsSchema>;

export const RecipeSchema = z.object({
  /** Unique identifier (kebab-case). */
  id: z.string().min(1),
  /** Human-readable display name. */
  name: z.string().min(1),
  /** One-line description. */
  description: z.string().min(1),
  /** Shown in preview cards. */
  previewText: z.string().min(1),
  /** Which render engines this recipe targets. */
  engines: z.array(EngineSchema).min(1),
  /** Scene kinds this recipe produces. */
  sceneKinds: z.array(SceneKindSchema).min(1),
  /** Short list of example use-cases. */
  useCases: z.array(z.string()).min(1),
  /** Allowed / expected inputs. */
  inputs: RecipeInputsSchema.optional(),
  /** Transition pack identifier. */
  transitionPack: z.string().optional(),
  /** Review rule slugs to apply. */
  reviewRules: z.array(z.string()).optional(),
  /** Sort / display weight (higher = first). */
  sortWeight: z.number().int().optional().default(0),
});
export type Recipe = z.infer<typeof RecipeSchema>;

/** Display-only helpers extracted from a Recipe for card rendering. */
export interface RecipeDisplayMeta {
  id: string;
  name: string;
  description: string;
  previewText: string;
  engines: Engine[];
  sceneKinds: SceneKind[];
  useCases: string[];
  sortWeight: number;
}

export function toDisplayMeta(r: Recipe): RecipeDisplayMeta {
  return {
    id: r.id,
    name: r.name,
    description: r.description,
    previewText: r.previewText,
    engines: r.engines,
    sceneKinds: r.sceneKinds,
    useCases: r.useCases,
    sortWeight: r.sortWeight ?? 0,
  };
}

/** Validate a recipe. Throws on invalid. */
export function validateRecipe(r: unknown): Recipe {
  return RecipeSchema.parse(r);
}

/** Validate an array of recipes. */
export function validateRecipeRegistry(r: unknown): Recipe[] {
  return z.array(RecipeSchema).parse(r);
}
