/**
 * Recipe registry — showcase-inspired recipes derived from study doc pattern map.
 *
 * Each recipe maps a Remotion showcase prompt to a VideoForge recipe:
 * - preferred engine(s)
 * - scene kinds it produces
 * - use-case examples
 * - preview text for card display
 */

import type { Recipe } from "./types";

export const recipeRegistry: Recipe[] = [
  {
    id: "travel-route-3d",
    name: "Travel Route with 3D Landmarks",
    description: "Animated travel route on map with 3D landmark overlays and camera fly-through",
    previewText:
      "Map-based travel animation. Route path draws across terrain, 3D landmarks pop at each waypoint. Camera arcs between locations.",
    engines: ["remotion"],
    sceneKinds: ["map3d", "title", "outro"],
    useCases: ["Travel vlogs", "Geography content", "Trip highlights"],
    transitionPack: "smooth",
    sortWeight: 90,
  },
  {
    id: "news-highlight",
    name: "News Article Headline Highlight",
    description: "Focus attention on key text with blur/unblur, markers, and perspective transform",
    previewText:
      "Document-style reveal. Background blurs, headline sharpens with animated marker overlay. Perspective transform adds depth.",
    engines: ["remotion"],
    sceneKinds: ["document-highlight", "title"],
    useCases: ["News summaries", "Article promos", "Quote highlights"],
    transitionPack: "quick",
    sortWeight: 85,
  },
  {
    id: "product-demo",
    name: "Product Demo — Screenflow",
    description: "Screen mockup walkthrough with cursor, feature callouts, and UI replication",
    previewText:
      "App UI simulation. Mockup screens with animated cursor, feature callout bubbles, smooth transitions between steps.",
    engines: ["remotion"],
    sceneKinds: ["screenflow", "title", "outro"],
    useCases: ["SaaS demos", "App store previews", "Feature announcements"],
    transitionPack: "smooth",
    sortWeight: 80,
  },
  {
    id: "launch-video",
    name: "Launch Video — Multi-Sequence",
    description: "High-energy multi-sequence narrative with terminal, cards, and layered promo scenes",
    previewText:
      "Fast-paced promo. Terminal typing effect, animated stat cards, layered scenes building to call-to-action.",
    engines: ["remotion", "animotion"],
    sceneKinds: ["promo", "title", "outro"],
    useCases: ["Product launches", "Startup promos", "Event teasers"],
    transitionPack: "dynamic",
    sortWeight: 75,
  },
  {
    id: "cinematic-intro",
    name: "Cinematic Tech Intro",
    description: "3D text, particle effects, glass HUD overlay, and scanner line tech aesthetic",
    previewText:
      "High-impact opener. 3D text floats in particle field, glass HUD elements slide in, scanner lines sweep across.",
    engines: ["remotion"],
    sceneKinds: ["hero-intro", "title"],
    useCases: ["Channel intros", "Tech brand videos", "Conference openers"],
    transitionPack: "dynamic",
    reviewRules: ["check-readability", "check-motion-sickness"],
    sortWeight: 70,
  },
  {
    id: "cta-overlay",
    name: "Transparent CTA Overlay",
    description: "Transparent export with lower-third CTA, subscribe button, and outro overlay",
    previewText:
      "Clean overlay card. Lower-third style call-to-action over existing footage. Supports transparent background export.",
    engines: ["remotion"],
    sceneKinds: ["overlay-cta", "outro"],
    useCases: ["YouTube end screens", "CTA overlays", "Lower-third titles"],
    transitionPack: "quick",
    sortWeight: 65,
  },
  {
    id: "rocket-timeline",
    name: "Rocket Launches Timeline",
    description: "Timeline with curved path motion showing launch sequences and milestones",
    previewText:
      "Trajectory-based timeline. Events animate along curved path, milestone markers with dates, countdown sequences.",
    engines: ["remotion", "manim"],
    sceneKinds: ["trajectory-timeline", "timeline", "title"],
    useCases: ["Historical timelines", "Project roadmaps", "Launch sequences"],
    transitionPack: "smooth",
    sortWeight: 60,
  },
  {
    id: "real-estate-metrics",
    name: "Real Estate Investing Showcase",
    description: "Counter animations, lower-third stats, and footage overlays for property metrics",
    previewText:
      "Property highlight reel. Animated counters show ROI stats, lower-thirds overlay property details, footage crossfades.",
    engines: ["remotion"],
    sceneKinds: ["real-estate", "title", "outro"],
    useCases: ["Real estate listings", "Property highlights", "Investment summaries"],
    transitionPack: "smooth",
    sortWeight: 55,
  },
  {
    id: "3d-ranking",
    name: "Three.js Top Games Ranking",
    description: "3D ranking bars with camera fly-through and podium animation",
    previewText:
      "3D leaderboard. Bars rise in perspective space, camera sweeps across ranked entries, podium at final placement.",
    engines: ["remotion"],
    sceneKinds: ["3d-ranking", "title"],
    useCases: ["Leaderboards", "Top 10 lists", "Ranking reveals"],
    transitionPack: "dynamic",
    sortWeight: 50,
  },
  {
    id: "chart-dual",
    name: "Bar + Line Chart Combined",
    description: "Hybrid chart animation with combined bar and line series on shared axis",
    previewText:
      "Dual-axis chart. Bar and line series animate simultaneously, tooltip callouts, axis labels with grid overlay.",
    engines: ["manim", "remotion"],
    sceneKinds: ["dual-chart", "chart", "title"],
    useCases: ["Financial reports", "Analytics dashboards", "Comparison data"],
    transitionPack: "smooth",
    reviewRules: ["check-axis-labels", "check-data-accuracy"],
    sortWeight: 45,
  },
  {
    id: "audio-reactive-viz",
    name: "Audio-Reactive Visualizer",
    description: "Music-responsive visuals with waveform, bars, and particle effects synced to audio",
    previewText:
      "Beat-synced animation. Waveform responds to audio amplitude, frequency bars pulse, particles dance to rhythm.",
    engines: ["remotion"],
    sceneKinds: ["audio-reactive", "title"],
    useCases: ["Music videos", "Podcast visuals", "Audio promos"],
    transitionPack: "dynamic",
    sortWeight: 40,
  },
  {
    id: "code-walkthrough",
    name: "Code Walkthrough with Diff",
    description: "Side-by-side code comparison with syntax highlighting and diff markers",
    previewText:
      "Readable code tour. Old/new side-by-side diff, animated highlight lines, language-tagged header bar.",
    engines: ["remotion", "animotion"],
    sceneKinds: ["code", "diff", "title", "outro"],
    useCases: ["Tutorials", "PR walkthroughs", "Tech talks"],
    transitionPack: "quick",
    reviewRules: ["check-code-visible"],
    sortWeight: 35,
  },
  {
    id: "diagram-flow",
    name: "System Diagram Flow",
    description: "Animated architecture diagram with node reveal and edge drawing",
    previewText:
      "Architecture walkthrough. Nodes fade in, edges draw between connected services, labels appear on hover sequence.",
    engines: ["manim", "animotion"],
    sceneKinds: ["diagram", "title"],
    useCases: ["Architecture docs", "System design videos", "Process flows"],
    transitionPack: "smooth",
    sortWeight: 30,
  },
  {
    id: "bullet-exec-summary",
    name: "Executive Summary — Bullet Points",
    description: "Clean bullet-point reveal with animated counters and takeaway highlights",
    previewText:
      "Concise summary. Bullets animate in sequence, key numbers count up, final takeaway emphasized with accent color.",
    engines: ["remotion", "animotion"],
    sceneKinds: ["bullet", "title", "outro"],
    useCases: ["Executive summaries", "Key takeaways", "Meeting recaps"],
    transitionPack: "quick",
    sortWeight: 25,
  },
];

/** Sorted copy (highest weight first). */
export function getSortedRecipes(): Recipe[] {
  return [...recipeRegistry].sort((a, b) => (b.sortWeight ?? 0) - (a.sortWeight ?? 0));
}

/** Look up recipe by id. */
export function getRecipeById(id: string): Recipe | undefined {
  return recipeRegistry.find((r) => r.id === id);
}

/** Filter recipes by engine. */
export function getRecipesByEngine(engine: string): Recipe[] {
  return recipeRegistry.filter((r) => r.engines.includes(engine as any));
}

/** Filter recipes that contain a given scene kind. */
export function getRecipesBySceneKind(kind: string): Recipe[] {
  return recipeRegistry.filter((r) => r.sceneKinds.includes(kind as any));
}

/** Collect all unique engines across all recipes. */
export function getAllEngines(): string[] {
  const set = new Set<string>();
  for (const r of recipeRegistry) r.engines.forEach((e) => set.add(e));
  return [...set].sort();
}

/** Collect all unique scene kinds across all recipes. */
export function getAllSceneKinds(): string[] {
  const set = new Set<string>();
  for (const r of recipeRegistry) r.sceneKinds.forEach((s) => set.add(s));
  return [...set].sort();
}

/** Collect all unique use-cases across all recipes. */
export function getAllUseCases(): string[] {
  const set = new Set<string>();
  for (const r of recipeRegistry) r.useCases.forEach((u) => set.add(u));
  return [...set].sort();
}
