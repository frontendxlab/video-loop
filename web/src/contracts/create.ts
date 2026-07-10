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
  provider: z.enum(["openai","anthropic","google","groq","deepseek","9router","custom"]).default("9router"),
  model: z.string().default("ocg/deepseek-v4-flash"),
  maxDuration: z.number().positive().default(180),
  fps: z.number().positive().default(30),
});
export type CreateOptions = z.infer<typeof CreateOptionsSchema>;

// ── Genre template types ───────────────────────────────────────────

export const TemplateSceneSchema = z.object({
  sceneType: z.string(),
  title: z.string(),
  description: z.string(),
  durationSeconds: z.number().default(4.0),
});
export type TemplateScene = z.infer<typeof TemplateSceneSchema>;

export const VideoTemplateSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  icon: z.string(),
  category: z.string(),
  scenes: z.array(TemplateSceneSchema),
  tags: z.array(z.string()),
});
export type VideoTemplate = z.infer<typeof VideoTemplateSchema>;

export const GENRE_TEMPLATES: VideoTemplate[] = [
  {
    id: "explainer",
    name: "Explainer",
    description: "Explain concept with diagrams, key points, and clear narration",
    icon: "lightbulb",
    category: "educational",
    scenes: [
      { sceneType: "title", title: "Topic Intro", description: "Opening title introducing the topic", durationSeconds: 4.0 },
      { sceneType: "diagram", title: "How It Works", description: "Visual diagram explaining core concept", durationSeconds: 5.0 },
      { sceneType: "bullets", title: "Key Takeaways", description: "Main takeaways highlighted in bullet form", durationSeconds: 4.0 },
      { sceneType: "outro", title: "Summary & Next Steps", description: "Recap and further resources", durationSeconds: 4.0 },
    ],
    tags: ["explain", "concept", "introduction", "overview", "educational"],
  },
  {
    id: "tutorial",
    name: "Tutorial",
    description: "Step-by-step walkthrough with examples and clear instructions",
    icon: "book-open",
    category: "educational",
    scenes: [
      { sceneType: "title", title: "Tutorial Title", description: "Opening title with topic and goal", durationSeconds: 4.0 },
      { sceneType: "code", title: "Step-by-Step", description: "Walk through implementation with code examples", durationSeconds: 8.0 },
      { sceneType: "bullets", title: "Key Takeaways", description: "Important points highlighted", durationSeconds: 4.0 },
      { sceneType: "outro", title: "Next Steps", description: "Where to go from here", durationSeconds: 4.0 },
    ],
    tags: ["tutorial", "walkthrough", "how-to", "guide", "steps", "learn"],
  },
  {
    id: "product-demo",
    name: "Product Demo",
    description: "Showcase product features with callouts, comparisons, and CTA",
    icon: "monitor",
    category: "marketing",
    scenes: [
      { sceneType: "title", title: "Product Intro", description: "Opening with product name and tagline", durationSeconds: 4.0 },
      { sceneType: "comparison", title: "Feature 1", description: "First key feature with highlight callouts", durationSeconds: 6.0 },
      { sceneType: "comparison", title: "Feature 2", description: "Second key feature demonstration", durationSeconds: 6.0 },
      { sceneType: "outro", title: "Call to Action", description: "CTA with next steps for the viewer", durationSeconds: 4.0 },
    ],
    tags: ["product", "demo", "showcase", "feature", "marketing"],
  },
  {
    id: "marketing",
    name: "Marketing",
    description: "Promotional video with hook, problem-solution, and strong CTA",
    icon: "megaphone",
    category: "marketing",
    scenes: [
      { sceneType: "title", title: "Hook", description: "Attention-grabbing opening hook", durationSeconds: 4.0 },
      { sceneType: "bullets", title: "The Problem", description: "Problem statement that resonates", durationSeconds: 5.0 },
      { sceneType: "comparison", title: "The Solution", description: "Solution presented with before/after", durationSeconds: 6.0 },
      { sceneType: "outro", title: "Call to Action", description: "Strong closing with CTA", durationSeconds: 4.0 },
    ],
    tags: ["marketing", "promo", "promotional", "hype", "campaign"],
  },
  {
    id: "storytelling",
    name: "Storytelling",
    description: "Narrative-driven video with emotional arc and story structure",
    icon: "scroll-text",
    category: "narrative",
    scenes: [
      { sceneType: "title", title: "Setup", description: "Establish context and characters", durationSeconds: 4.0 },
      { sceneType: "bullets", title: "Conflict", description: "Present the challenge or stakes", durationSeconds: 5.0 },
      { sceneType: "quote", title: "Resolution", description: "Climax and resolution of the story", durationSeconds: 5.0 },
      { sceneType: "outro", title: "Reflection", description: "Closing reflections and call to action", durationSeconds: 4.0 },
    ],
    tags: ["story", "narrative", "emotional", "journey", "arc"],
  },
  {
    id: "data-story",
    name: "Data Story",
    description: "Data-driven narrative with charts, metrics, and insights",
    icon: "bar-chart-3",
    category: "data",
    scenes: [
      { sceneType: "title", title: "Context", description: "Set the data context and motivation", durationSeconds: 4.0 },
      { sceneType: "chart", title: "Data Overview", description: "Key metrics and data visualization", durationSeconds: 5.0 },
      { sceneType: "chart", title: "Deep Dive", description: "Detailed breakdown of specific data points", durationSeconds: 6.0 },
      { sceneType: "bullets", title: "Insights", description: "Actionable insights and conclusions", durationSeconds: 4.0 },
    ],
    tags: ["data", "chart", "metrics", "analytics", "statistics", "insights"],
  },
  {
    id: "comparison",
    name: "Comparison",
    description: "Side-by-side comparison of options, versions, or approaches",
    icon: "git-compare",
    category: "analysis",
    scenes: [
      { sceneType: "title", title: "Comparison Intro", description: "What is being compared and why", durationSeconds: 4.0 },
      { sceneType: "comparison", title: "Option A", description: "Overview of the first option", durationSeconds: 5.0 },
      { sceneType: "comparison", title: "Option B", description: "Overview of the second option", durationSeconds: 5.0 },
      { sceneType: "diff", title: "Verdict", description: "Summary verdict and recommendation", durationSeconds: 4.0 },
    ],
    tags: ["compare", "comparison", "vs", "versus", "difference", "migration"],
  },
  {
    id: "timeline",
    name: "Timeline",
    description: "Chronological walkthrough of events, history, or roadmap",
    icon: "clock",
    category: "narrative",
    scenes: [
      { sceneType: "title", title: "Timeline Intro", description: "Opening with the scope of events", durationSeconds: 4.0 },
      { sceneType: "timeline", title: "Event 1", description: "First key event or milestone", durationSeconds: 5.0 },
      { sceneType: "timeline", title: "Event 2", description: "Second key event or milestone", durationSeconds: 5.0 },
      { sceneType: "timeline", title: "Event 3", description: "Third key event or milestone", durationSeconds: 5.0 },
      { sceneType: "outro", title: "Summary & Outlook", description: "Wrap-up and future outlook", durationSeconds: 4.0 },
    ],
    tags: ["timeline", "history", "roadmap", "events", "chronological"],
  },
  {
    id: "review",
    name: "Review",
    description: "Honest review with pros/cons, rating, and final verdict",
    icon: "star",
    category: "analysis",
    scenes: [
      { sceneType: "title", title: "Review Intro", description: "What is being reviewed", durationSeconds: 4.0 },
      { sceneType: "bullets", title: "Pros", description: "What works well — pros", durationSeconds: 5.0 },
      { sceneType: "bullets", title: "Cons", description: "What could be improved — cons", durationSeconds: 5.0 },
      { sceneType: "outro", title: "Final Verdict", description: "Rating and final recommendation", durationSeconds: 4.0 },
    ],
    tags: ["review", "rating", "pros-cons", "verdict", "opinion"],
  },
];

export const CreateJobRequestSchema = z.object({
  prompt: z.string().min(10, "Prompt must be at least 10 characters"),
  options: CreateOptionsSchema,
  recipeId: z.string().optional(),
  templateIds: z.array(z.string()).optional(),
});
export type CreateJobRequest = z.infer<typeof CreateJobRequestSchema>;

export const SceneSuggestionSchema = z.object({
  kind: z.string(), title: z.string(), description: z.string(), reasoning: z.string(),
});
export type SceneSuggestion = z.infer<typeof SceneSuggestionSchema>;

export const SuggestedTemplateSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  icon: z.string(),
  category: z.string(),
  match_reason: z.string(),
  scene_count: z.number(),
});
export type SuggestedTemplate = z.infer<typeof SuggestedTemplateSchema>;

export const GrillResultSchema = z.object({
  refinedPrompt: z.string(),
  suggestedScenes: z.array(SceneSuggestionSchema),
  suggestedTemplates: z.array(SuggestedTemplateSchema).default([]),
  missingDetails: z.array(z.string()),
  confidence: z.number().min(0).max(1),
});
export type GrillResult = z.infer<typeof GrillResultSchema>;

// ── Template types ────────────────────────────────────────────────

export const TemplateSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  icon: z.string(),
  tags: z.array(z.string()),
  styleHints: z.array(z.string()),
});
export type Template = z.infer<typeof TemplateSchema>;

export const TEMPLATE_PRESETS: Template[] = [
  {
    id: "cinematic",
    name: "Cinematic",
    description: "Movie-like with dramatic pacing, smooth transitions, and widescreen feel",
    icon: "clapperboard",
    tags: ["dramatic", "polished", "slow-motion"],
    styleHints: ["Dramatic pacing", "Smooth transitions", "Depth of field"],
  },
  {
    id: "educational",
    name: "Educational",
    description: "Clear explanatory style with diagrams, annotations, and structured flow",
    icon: "graduation-cap",
    tags: ["explanatory", "structured", "annotations"],
    styleHints: ["Clear typography", "Step-by-step reveals", "Supporting diagrams"],
  },
  {
    id: "data-driven",
    name: "Data-driven",
    description: "Emphasize charts, graphs, and data visualization with precision animation",
    icon: "bar-chart-3",
    tags: ["charts", "statistics", "visualization"],
    styleHints: ["Chart-first layout", "Precision animation", "Data callouts"],
  },
  {
    id: "tutorial",
    name: "Tutorial",
    description: "Step-by-step walkthrough with numbered stages and highlight regions",
    icon: "book-open",
    tags: ["step-by-step", "walkthrough", "numbered"],
    styleHints: ["Numbered steps", "Highlight regions", "Progress indicators"],
  },
  {
    id: "social-clip",
    name: "Social clip",
    description: "Short, snappy format optimized for social media with bold captions",
    icon: "smartphone",
    tags: ["short", "bold", "captions"],
    styleHints: ["Bold captions", "Fast cuts", "Mobile-first framing"],
  },
  {
    id: "narrative",
    name: "Narrative",
    description: "Story-driven structure with beginning, middle, end and emotional arc",
    icon: "scroll-text",
    tags: ["story", "emotional", "arc"],
    styleHints: ["Story arc pacing", "Emotional beats", "Narrative overlay"],
  },
  {
    id: "minimalist",
    name: "Minimalist",
    description: "Clean, simple design with maximum whitespace and minimal distractions",
    icon: "sparkles",
    tags: ["clean", "simple", "whitespace"],
    styleHints: ["Maximum whitespace", "Minimal elements", "Subtle animations"],
  },
  {
    id: "dynamic",
    name: "Dynamic",
    description: "Fast-paced energetic style with frequent transitions and motion effects",
    icon: "zap",
    tags: ["fast-paced", "energetic", "transitions"],
    styleHints: ["Quick transitions", "Motion effects", "Energetic pacing"],
  },
];

// ── Multi-turn grill schemas ─────────────────────────────────────────

export const GrillStartResponseSchema = z.object({
  sessionId: z.string(),
  question: z.string(),
  questionId: z.string(),
  asked: z.number(),
  total: z.number(),
});
export type GrillStartResponse = z.infer<typeof GrillStartResponseSchema>;

export const GrillTurnResponseSchema = z.object({
  question: z.string().nullable(),
  questionId: z.string().nullable(),
  asked: z.number(),
  total: z.number(),
  done: z.boolean(),
  result: GrillResultSchema.nullable(),
});
export type GrillTurnResponse = z.infer<typeof GrillTurnResponseSchema>;

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
