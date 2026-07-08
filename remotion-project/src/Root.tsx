import { Composition } from "remotion";
import { z } from "zod";
import { VideoComposition } from "./compositions/VideoComposition";

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
  duration: z.number(),
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
  style: { primaryColor: "#4a90d9", font: "Inter", codeTheme: "poimandres" },
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
    </>
  );
};
