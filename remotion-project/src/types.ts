import { z } from "zod";

export const TitleSceneSchema = z.object({
  type: z.literal("title"),
  title: z.string().min(1),
  subtitle: z.string().optional(),
  duration: z.number().positive(),
});

export const CodeSceneSchema = z.object({
  type: z.literal("code"),
  code: z.string().min(1),
  lang: z.string(),
  highlightLines: z.array(z.number()).optional(),
  duration: z.number().positive(),
});

export const DiffSceneSchema = z.object({
  type: z.literal("diff"),
  oldCode: z.string(),
  newCode: z.string(),
  lang: z.string(),
  duration: z.number().positive(),
});

export const BulletSceneSchema = z.object({
  type: z.literal("bullet"),
  points: z.array(z.string()).min(2).max(5),
  duration: z.number().positive(),
});

export const ImageSceneSchema = z.object({
  type: z.literal("image"),
  src: z.string(),
  caption: z.string().optional(),
  duration: z.number().positive(),
});

export const ComparisonSceneSchema = z.object({
  type: z.literal("comparison"),
  labelBefore: z.string(),
  labelAfter: z.string(),
  duration: z.number().positive(),
});

export const DiagramSceneSchema = z.object({
  type: z.literal("diagram"),
  config: z.object({
    nodes: z.array(
      z.object({
        id: z.string(),
        label: z.string(),
        position: z.object({ row: z.number(), col: z.number() }),
      })
    ),
  }),
  duration: z.number().positive(),
});

export const OutroSceneSchema = z.object({
  type: z.literal("outro"),
  title: z.string(),
  cta: z.string().optional(),
  duration: z.number().positive(),
});

export const ChartSceneSchema = z.object({
  type: z.literal("chart"),
  chartType: z.enum(["bar", "line"]).default("bar"),
  title: z.string().optional(),
  data: z.array(z.object({ label: z.string(), value: z.number() })),
  yAxisLabel: z.string().optional(),
  duration: z.number().positive(),
});

export const TimelineSceneSchema = z.object({
  type: z.literal("timeline"),
  title: z.string().optional(),
  events: z.array(z.object({ label: z.string(), date: z.string().optional() })).min(1),
  duration: z.number().positive(),
});

export const SceneSchema = z.discriminatedUnion("type", [
  TitleSceneSchema,
  CodeSceneSchema,
  DiffSceneSchema,
  BulletSceneSchema,
  ImageSceneSchema,
  ComparisonSceneSchema,
  DiagramSceneSchema,
  OutroSceneSchema,
  ChartSceneSchema,
  TimelineSceneSchema,
]);

export const AudioTrackSchema = z.object({
  src: z.string(),
  startFrame: z.number(),
  duration: z.number(),
});

export const CaptionSchema = z.object({
  text: z.string(),
  startMs: z.number(),
  endMs: z.number(),
});

export const StyleSchema = z.object({
  primaryColor: z.string(),
  font: z.string(),
  codeTheme: z.string(),
});

export const InputPropsSchema = z.object({
  title: z.string().optional(),
  scenes: z.array(SceneSchema),
  audioTracks: z.array(AudioTrackSchema),
  captions: z.array(CaptionSchema),
  voice: z.string(),
  style: StyleSchema,
});

export type TitleScene = z.infer<typeof TitleSceneSchema>;
export type CodeScene = z.infer<typeof CodeSceneSchema>;
export type DiffScene = z.infer<typeof DiffSceneSchema>;
export type BulletScene = z.infer<typeof BulletSceneSchema>;
export type ImageScene = z.infer<typeof ImageSceneSchema>;
export type ComparisonScene = z.infer<typeof ComparisonSceneSchema>;
export type DiagramScene = z.infer<typeof DiagramSceneSchema>;
export type OutroScene = z.infer<typeof OutroSceneSchema>;
export type ChartScene = z.infer<typeof ChartSceneSchema>;
export type TimelineScene = z.infer<typeof TimelineSceneSchema>;
export type Scene = z.infer<typeof SceneSchema>;
export type AudioTrack = z.infer<typeof AudioTrackSchema>;
export type Caption = z.infer<typeof CaptionSchema>;
export type Style = z.infer<typeof StyleSchema>;
export type InputProps = z.infer<typeof InputPropsSchema>;
