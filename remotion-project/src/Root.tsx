import { Composition } from "remotion";
import { z } from "zod";
import { VideoComposition } from "./compositions/VideoComposition";
import { remotionStyleDefaults } from "./design-tokens";

const WordTimingSchema = z.object({
  text: z.string(),
  startMs: z.number(),
  endMs: z.number(),
});

const SceneSchema = z.object({
  type: z.string(),
  title: z.string().optional(),
  subtitle: z.string().optional(),
  code: z.string().optional(),
  lang: z.string().optional(),
  points: z.array(z.string()).optional(),
  src: z.string().optional(),
  caption: z.string().optional(),
  cta: z.string().optional(),
  text: z.string().optional(),
  nodeprefix: z.string().optional(),
  duration: z.number(),
  wordTimestamps: z.array(WordTimingSchema).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

const AudioTrackSchema = z.object({
  src: z.string(),
  startFrame: z.number(),
  durationFrames: z.number(),
});

const CaptionWordSchema = z.object({
  text: z.string(),
  startMs: z.number(),
  endMs: z.number(),
});

const InputPropsSchema = z.object({
  title: z.string(),
  scenes: z.array(SceneSchema),
  audioTracks: z.array(AudioTrackSchema),
  captions: z.array(CaptionWordSchema),
  voice: z.string(),
  style: z.object({
    primaryColor: z.string(),
    font: z.string(),
    codeTheme: z.string(),
  }),
});

const DEFAULT_PROPS = {
  title: "Video",
  scenes: [{ type: "title", title: "Video", duration: 90 }],
  audioTracks: [],
  captions: [],
  voice: "alba",
  style: remotionStyleDefaults,
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="VideoComposition"
        component={VideoComposition}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        schema={InputPropsSchema}
        defaultProps={DEFAULT_PROPS}
        calculateMetadata={async ({ props }) => {
          const total = (props.scenes || []).reduce((sum: number, s: any) => sum + (s.duration || 0), 0);
          return { durationInFrames: Math.max(total, 1) };
        }}
      />
      <Composition
        id="CodeWalkthrough"
        component={VideoComposition}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        schema={InputPropsSchema}
        defaultProps={DEFAULT_PROPS}
      />
      <Composition
        id="ChartComposition"
        component={VideoComposition}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        schema={InputPropsSchema}
        defaultProps={{
          title: "Chart",
          scenes: [{ type: "chart", chartType: "bar" as const, title: "Demo", data: [{ label: "A", value: 10 }, { label: "B", value: 20 }], duration: 120 }],
          audioTracks: [],
          captions: [],
          voice: "alba",
          style: remotionStyleDefaults,
        }}
      />
      <Composition
        id="ThreeComposition"
        component={VideoComposition}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        schema={InputPropsSchema}
        defaultProps={{
          title: "Three Demo",
          scenes: [{ type: "three", duration: 150 }],
          audioTracks: [],
          captions: [],
          voice: "alba",
          style: remotionStyleDefaults,
        }}
      />
      <Composition
        id="TimelineComposition"
        component={VideoComposition}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        schema={InputPropsSchema}
        defaultProps={{
          title: "Timeline",
          scenes: [{ type: "timeline", title: "Demo", events: [{ label: "Start", date: "2020" }, { label: "End", date: "2024" }], duration: 120 }],
          audioTracks: [],
          captions: [],
          voice: "alba",
          style: remotionStyleDefaults,
        }}
      />
    </>
  );
};
