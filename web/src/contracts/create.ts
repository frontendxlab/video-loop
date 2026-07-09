import { z } from "zod";

// ── Recipe types ─────────────────────────────────────────────────

export const RecipeAllowedInputSchema = z.object({
  key: z.string(),
  type: z.enum(["string", "number", "boolean", "array"]),
  required: z.boolean(),
  description: z.string(),
});
export type RecipeAllowedInput = z.infer<typeof RecipeAllowedInputSchema>;

export const RecipeSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  sceneKind: z.string(),
  preferredEngine: z.string(),
  fallbackEngines: z.array(z.string()),
  allowedInputs: z.array(RecipeAllowedInputSchema),
  entrance: z.string(),
  exit: z.string(),
  tags: z.array(z.string()),
});
export type Recipe = z.infer<typeof RecipeSchema>;

export const RECIPE_PRESETS: Recipe[] = [
  {
    id: "hero-intro",
    name: "Hero intro",
    description: "Cinematic hero title with HUD overlay — 3D text, particle background, glow effects",
    sceneKind: "title",
    preferredEngine: "remotion",
    fallbackEngines: [],
    allowedInputs: [
      { key: "title", type: "string", required: true, description: "Hero title text" },
      { key: "subtitle", type: "string", required: false, description: "Subtitle line" },
    ],
    entrance: "glitch_in",
    exit: "shatter_out",
    tags: ["hero", "title", "3d", "glow"],
  },
  {
    id: "document-highlight",
    name: "Document highlight",
    description: "Document-style title card with focus phrase emphasis and blur transitions",
    sceneKind: "title",
    preferredEngine: "remotion",
    fallbackEngines: [],
    allowedInputs: [
      { key: "title", type: "string", required: true, description: "Document title" },
      { key: "body_snippet", type: "string", required: true, description: "Body text with highlight" },
      { key: "focus_phrase", type: "string", required: true, description: "Phrase to highlight (must appear in body_snippet)" },
    ],
    entrance: "unfold",
    exit: "blur_out",
    tags: ["text", "highlight", "document", "news"],
  },
  {
    id: "screenflow",
    name: "Screenflow",
    description: "Product demo with zoom, pan callouts — screenshot-based walkthrough",
    sceneKind: "comparison",
    preferredEngine: "remotion",
    fallbackEngines: [],
    allowedInputs: [
      { key: "screenshot_url", type: "string", required: true, description: "Screenshot URL or path" },
      { key: "callout_text", type: "string", required: false, description: "Callout annotation" },
    ],
    entrance: "zoom_in",
    exit: "slide_out_left",
    tags: ["product", "demo", "screenflow", "ui"],
  },
  {
    id: "map3d",
    name: "Map 3D",
    description: "3D map fly-through with route path, markers, and geospatial context",
    sceneKind: "map3d",
    preferredEngine: "manim",
    fallbackEngines: [],
    allowedInputs: [
      { key: "coordinates", type: "array", required: true, description: "Array of [lat, lng] points" },
      { key: "markers", type: "array", required: false, description: "Array of marker objects with label" },
    ],
    entrance: "fly_in",
    exit: "fade_out",
    tags: ["geospatial", "3d", "travel", "map"],
  },
  {
    id: "trajectory-timeline",
    name: "Trajectory timeline",
    description: "Animated timeline with path trajectory and event markers along axis",
    sceneKind: "timeline",
    preferredEngine: "manim",
    fallbackEngines: [],
    allowedInputs: [
      { key: "events", type: "array", required: true, description: "Array of {label, date, description} objects" },
    ],
    entrance: "slide_in_right",
    exit: "shrink_to_right",
    tags: ["timeline", "trajectory", "path", "motion"],
  },
  {
    id: "3d-ranking",
    name: "3D ranking",
    description: "3D bar ranking chart with camera fly-through revealing each bar",
    sceneKind: "chart",
    preferredEngine: "remotion",
    fallbackEngines: ["manim"],
    allowedInputs: [
      { key: "items", type: "array", required: true, description: "Array of {label, value} objects sorted by rank" },
    ],
    entrance: "rise_up",
    exit: "fade_out",
    tags: ["3d", "ranking", "bars", "chart", "data"],
  },
  {
    id: "dual-chart",
    name: "Dual chart",
    description: "Dual-axis chart combining bar and line series with annotations",
    sceneKind: "chart",
    preferredEngine: "manim",
    fallbackEngines: [],
    allowedInputs: [
      { key: "bar_series", type: "array", required: true, description: "Array of {label, value} for bars" },
      { key: "line_series", type: "array", required: true, description: "Array of {label, value} for line" },
    ],
    entrance: "grow_from_bottom",
    exit: "fade_out",
    tags: ["chart", "dual", "bar", "line", "data"],
  },
  {
    id: "audio-reactive",
    name: "Audio reactive",
    description: "Audio waveform visualizer with reactive bar heights synced to music",
    sceneKind: "title",
    preferredEngine: "remotion",
    fallbackEngines: [],
    allowedInputs: [
      { key: "audio_src", type: "string", required: true, description: "Audio file URL or path" },
    ],
    entrance: "wave_in",
    exit: "fade_out",
    tags: ["audio", "reactive", "music", "waveform", "visualizer"],
  },
  {
    id: "overlay-cta",
    name: "Overlay CTA",
    description: "Transparent overlay with CTA button, lower-third title — exports with alpha channel for compositing",
    sceneKind: "outro",
    preferredEngine: "remotion",
    fallbackEngines: [],
    allowedInputs: [
      { key: "title", type: "string", required: true, description: "CTA title text" },
      { key: "button_text", type: "string", required: false, description: "Button label" },
    ],
    entrance: "slide_up",
    exit: "fade_out",
    tags: ["cta", "overlay", "lower-third", "transparent"],
  },
];

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
  recipeId: z.string().optional(),
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
