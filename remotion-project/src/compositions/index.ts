export type SceneType =
  | "title"
  | "code"
  | "diff"
  | "bullet"
  | "image"
  | "comparison"
  | "diagram"
  | "outro";

export interface SceneBase {
  type: SceneType;
  duration: number;
}

export interface CompositionRegistry {
  scenes: SceneBase[];
}

export const COMPOSITION_IDS = [
  "CodeWalkthrough",
  "PRSummary",
  "IssueExplainer",
  "ChangelogVideo",
] as const;

export type CompositionId = (typeof COMPOSITION_IDS)[number];

export const SCENE_TYPES: SceneType[] = [
  "title",
  "code",
  "diff",
  "bullet",
  "image",
  "comparison",
  "diagram",
  "outro",
];
