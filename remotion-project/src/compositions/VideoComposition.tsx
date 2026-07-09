import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame } from "remotion";
import { CaptionOverlay } from "../captions/CaptionOverlay";
import { TitleScene } from "../scenes/TitleScene";
import { CodeScene } from "../scenes/CodeScene";
import { BulletScene } from "../scenes/BulletScene";
import { ImageScene } from "../scenes/ImageScene";
import { OutroScene } from "../scenes/OutroScene";
import { AnimatedMindMap, MindMapNode } from "../components/AnimatedMindMap";
import { AnimatedCodeLines } from "../components/AnimatedCodeLines";
import { ChartScene } from "../components/scenes/ChartScene";
import { TimelineScene } from "../components/scenes/TimelineScene";

interface WordTimingData {
  text: string;
  startMs: number;
  endMs: number;
}

interface SceneData {
  type: string;
  title?: string;
  subtitle?: string;
  code?: string;
  lang?: string;
  points?: string[];
  src?: string;
  caption?: string;
  cta?: string;
  text?: string;
  nodeprefix?: string;
  duration: number;
  wordTimestamps?: WordTimingData[];
  sceneStartFrame?: number;
  root?: MindMapNode;
  chartType?: "bar" | "line";
  data?: { label: string; value: number }[];
  yAxisLabel?: string;
  events?: { label: string; date?: string }[];
}

interface AudioTrack {
  src: string;
  startFrame: number;
  durationFrames: number;
}

interface CaptionWord {
  text: string;
  startMs: number;
  endMs: number;
}

interface VideoCompositionProps {
  title: string;
  scenes: SceneData[];
  audioTracks: AudioTrack[];
  captions: CaptionWord[];
  voice: string;
  style: { primaryColor: string; font: string; codeTheme: string };
}

const SceneRenderer: React.FC<{ scene: SceneData; frameOffset: number }> = ({ scene, frameOffset }) => {
  const dur = scene.duration;
  const ts = scene.wordTimestamps;
  const sf = frameOffset;
  switch (scene.type) {
    case "title":
      return <TitleScene title={scene.title || ""} subtitle={scene.subtitle} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "code":
      return <CodeScene code={scene.code || ""} lang={scene.lang || "text"} highlightLines={[]} caption={scene.caption} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "bullet":
      return <BulletScene points={scene.points || []} title={scene.title || scene.caption} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "image":
      return <ImageScene src={scene.src || ""} caption={scene.caption} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "outro":
      return <OutroScene title={scene.title || "Thank You"} cta={scene.cta} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "mindmap":
      return <AnimatedMindMap root={scene.root || { id: "root", label: scene.title || "", children: [], timing: ts?.[0] }} wordTimestamps={ts || []} sceneStartFrame={sf} />;
    case "code-walkthrough":
      return <AnimatedCodeLines code={scene.code || ""} lang={scene.lang || "text"} wordTimestamps={ts || []} sceneStartFrame={sf} title={scene.title} />;
    case "chart":
      return <ChartScene chartType={scene.chartType || "bar"} title={scene.title} data={scene.data || []} yAxisLabel={scene.yAxisLabel} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "timeline":
      return <TimelineScene title={scene.title} events={scene.events || []} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    default:
      return (
        <AbsoluteFill style={{ background: "linear-gradient(135deg, #0f0f23, #1a1a3e)", justifyContent: "center", alignItems: "center", color: "white", fontSize: 32 }}>
          {scene.title || scene.caption || ""}
        </AbsoluteFill>
      );
  }
};

const ScopedCaption: React.FC<{ words: CaptionWord[]; sceneStartFrame: number; sceneEndFrame: number }> = ({
  words, sceneStartFrame, sceneEndFrame,
}) => {
  const frame = useCurrentFrame();
  if (frame < sceneStartFrame || frame >= sceneEndFrame) return null;
  const sceneMsStart = (sceneStartFrame / 30) * 1000;
  const sceneMsEnd = (sceneEndFrame / 30) * 1000;
  const sceneWords = words.filter(w => w.startMs >= sceneMsStart && w.startMs < sceneMsEnd);
  return <CaptionOverlay words={sceneWords} fps={30} />;
};

export const VideoComposition: React.FC<VideoCompositionProps> = ({ scenes, audioTracks, captions }) => {
  if (!scenes || scenes.length === 0) {
    return <AbsoluteFill style={{ background: "#000" }} />;
  }

  let frameOffset = 0;
  const sceneElements: React.ReactNode[] = [];
  const audioElements: React.ReactNode[] = [];
  const captionElements: React.ReactNode[] = [];

  for (let i = 0; i < scenes.length; i++) {
    const dur = scenes[i].duration;
    if (dur <= 0) continue;

    sceneElements.push(
      <Sequence key={`scene-${i}`} from={frameOffset} durationInFrames={dur}>
        <SceneRenderer scene={scenes[i]} frameOffset={frameOffset} />
      </Sequence>
    );

    const audioTrack = audioTracks[i];
    if (audioTrack) {
      audioElements.push(
        <Sequence key={`audio-seq-${i}`} from={frameOffset} durationInFrames={dur}>
          <Audio src={staticFile(audioTrack.src)} />
        </Sequence>
      );
    }

    captionElements.push(
      <ScopedCaption
        key={`cap-${i}`}
        words={captions}
        sceneStartFrame={frameOffset}
        sceneEndFrame={frameOffset + dur}
      />
    );

    frameOffset += dur;
  }

  return (
    <AbsoluteFill style={{ background: "#0f0f23" }}>
      {sceneElements}
      {audioElements}
      {captionElements}
    </AbsoluteFill>
  );
};
