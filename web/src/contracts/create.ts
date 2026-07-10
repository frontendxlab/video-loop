import { z } from "zod";

// ── Recipe types ─────────────────────────────────────────────────

export const RecipeAllowedInputSchema = z.object({
  key: z.string(),
  type: z.enum(["string", "number", "boolean", "array"]),
  required: z.boolean(),
  description: z.string(),
});
export type RecipeAllowedInput = z.infer<typeof RecipeAllowedInputSchema>;

export const RecipeEngineBadgeSchema = z.object({
  engine: z.string(),
  label: z.string(),
  variant: z.enum(["default", "secondary", "outline", "success", "warning"]).optional(),
});
export type RecipeEngineBadge = z.infer<typeof RecipeEngineBadgeSchema>;

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
  // Showcase metadata
  useCases: z.array(z.string()),
  motionHints: z.object({
    entrance: z.string(),
    exit: z.string(),
  }),
  reviewHints: z.array(z.string()),
  engineBadges: z.array(RecipeEngineBadgeSchema),
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
    useCases: ["Video intros", "Channel branding", "Opening sequences"],
    motionHints: { entrance: "Glitch distortion reveal with scan lines", exit: "Shatter into particles and fade" },
    reviewHints: ["Verify 3D text renders without z-fighting", "Check glow effect intensity on target display"],
    engineBadges: [{ engine: "remotion", label: "Primary renderer", variant: "default" }],
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
    useCases: ["News segments", "Documentary titles", "Quote displays"],
    motionHints: { entrance: "Document unrolls from center", exit: "Content blurs and dissolves" },
    reviewHints: ["Confirm focus_phrase appears in body_snippet", "Check highlight color contrast"],
    engineBadges: [{ engine: "remotion", label: "Primary renderer", variant: "default" }],
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
    useCases: ["Product demos", "UI walkthroughs", "Tutorials"],
    motionHints: { entrance: "Zoom in from screenshot center", exit: "Slide left to reveal next scene" },
    reviewHints: ["Verify screenshot resolution matches output", "Check callout text legibility at target size"],
    engineBadges: [{ engine: "remotion", label: "Primary renderer", variant: "default" }],
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
    useCases: ["Geospatial stories", "Travel routes", "Location-based narratives"],
    motionHints: { entrance: "Camera flies down from high orbit to target location", exit: "Fade to black with route overlay" },
    reviewHints: ["Verify camera path doesn't clip through terrain", "Check marker labels are readable at zoom level"],
    engineBadges: [{ engine: "manim", label: "Primary renderer", variant: "default" }],
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
    useCases: ["Historical timelines", "Project roadmaps", "Sequence of events"],
    motionHints: { entrance: "Timeline slides in from right edge", exit: "Timeline shrinks and collapses to right" },
    reviewHints: ["Verify event markers align with dates", "Check trajectory path doesn't overlap labels"],
    engineBadges: [{ engine: "manim", label: "Primary renderer", variant: "default" }],
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
    useCases: ["Leaderboards", "Top-N lists", "Competitive rankings"],
    motionHints: { entrance: "Bars rise from floor with sequential reveal", exit: "Scene fades to neutral" },
    reviewHints: ["Verify bars are sorted by value descending", "Check camera fly-through targets each bar"],
    engineBadges: [
      { engine: "remotion", label: "Primary renderer", variant: "default" },
      { engine: "manim", label: "Fallback renderer", variant: "outline" },
    ],
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
    useCases: ["Financial reports", "Data comparisons", "Trend analysis"],
    motionHints: { entrance: "Bar and line series grow from bottom axis", exit: "Both series fade simultaneously" },
    reviewHints: ["Verify dual axes have separate scales", "Check bar and line data points align on x-axis"],
    engineBadges: [{ engine: "manim", label: "Primary renderer", variant: "default" }],
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
    useCases: ["Music visualizations", "Podcast intros", "Audio branding"],
    motionHints: { entrance: "Waveform pulses in from left with beat sync", exit: "Waveform fades and disperses" },
    reviewHints: ["Verify waveform syncs with audio peaks", "Check bar count matches FFT bin resolution"],
    engineBadges: [{ engine: "remotion", label: "Primary renderer", variant: "default" }],
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
    useCases: ["End screens", "Call-to-action overlays", "Lower thirds"],
    motionHints: { entrance: "Content slides up from bottom edge", exit: "Fades to transparent for compositing" },
    reviewHints: ["Verify alpha channel exports correctly", "Check text contrast over varied background colors"],
    engineBadges: [{ engine: "remotion", label: "Primary renderer", variant: "default" }],
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
  provider: z.enum(["openai","anthropic","google","deepseek","9router","custom"]).default("9router"),
  model: z.string().default("ocg/deepseek-v4-flash"),
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
  voice: "alba", provider: "9router", model: "ocg/deepseek-v4-flash", maxDuration: 180, fps: 30,
};

export const CREATE_STAGES = [
  { id: "grill", label: "Grill prompt" },
  { id: "plan", label: "Plan scenes" },
  { id: "audio", label: "Generate audio" },
  { id: "render", label: "Render video" },
  { id: "review", label: "Review quality" },
] as const;
