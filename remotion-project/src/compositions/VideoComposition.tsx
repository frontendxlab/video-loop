import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame } from "remotion";
import { CaptionOverlay } from "../captions/CaptionOverlay";
import { TitleScene } from "../scenes/TitleScene";
import { CodeScene } from "../scenes/CodeScene";
import { BulletScene } from "../scenes/BulletScene";
import { ImageScene } from "../scenes/ImageScene";
import { OutroScene } from "../scenes/OutroScene";
import { Hero3DScene } from "../scenes/Hero3DScene";
import { ThreeSceneExample } from "../scenes/ThreeSceneExample";
import { LowerThird } from "../scenes/LowerThird";
import { OverlayCTA } from "../scenes/OverlayCTA";
import { ScreenflowScene } from "../scenes/ScreenflowScene";
import { AnimatedMindMap, MindMapNode } from "../components/AnimatedMindMap";
import { AnimatedCodeLines } from "../components/AnimatedCodeLines";
import { ChartScene } from "../components/scenes/ChartScene";
import { DualChartScene } from "../components/scenes/DualChartScene";
import { TimelineScene } from "../components/scenes/TimelineScene";
import { KineticTextScene } from "../components/scenes/KineticTextScene";
import { AudioVizScene } from "../scenes/AudioVizScene";
import { MapScene } from "../scenes/MapScene";
import { colors, fonts } from "../design-tokens";

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
  barData?: { label: string; value: number }[];
  lineData?: { label: string; value: number }[];
  barLabel?: string;
  lineLabel?: string;
  leftAxisLabel?: string;
  rightAxisLabel?: string;
  lines?: { text: string; highlightWords?: string[]; animation?: string }[];
  lineAnimation?: "sequential" | "simultaneous";
  device?: "phone" | "browser";
  screenshot?: string;
  callouts?: { text: string; x: number; y: number }[];
  cursorPath?: { x: number; y: number; frame: number }[];
  audioSrc?: string;
  variant?: "waveform" | "spectrum";
  barCount?: number;
  centerLat?: number;
  centerLng?: number;
  zoom?: number;
  style?: string;
  markers?: { lat: number; lng: number; label?: string; color?: string }[];
  routes?: { points: { lat: number; lng: number }[]; color?: string; width?: number }[];
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
    case "dualChart":
      return <DualChartScene title={scene.title} barData={scene.barData || []} lineData={scene.lineData || []} barLabel={scene.barLabel} lineLabel={scene.lineLabel} leftAxisLabel={scene.leftAxisLabel} rightAxisLabel={scene.rightAxisLabel} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "timeline":
      return <TimelineScene title={scene.title} events={scene.events || []} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "lowerThird":
      return <LowerThird title={scene.title || ""} subtitle={scene.subtitle} slideDirection={(scene as any).slideDirection} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "overlayCTA":
      return <OverlayCTA title={scene.title || ""} subtitle={scene.subtitle} cta={scene.cta} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "kinetic":
      return <KineticTextScene lines={scene.lines || [{ text: "" }]} lineAnimation={scene.lineAnimation} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "hero3d":
      return <Hero3DScene title={scene.title || ""} subtitle={scene.subtitle} deviceType={(scene as any).deviceType} duration={dur} />;
    case "screenflow":
      return <ScreenflowScene device={scene.device || "browser"} screenshot={scene.screenshot || ""} title={scene.title} callouts={scene.callouts || []} cursorPath={scene.cursorPath || []} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "three":
      return <ThreeSceneExample duration={dur} />;
    case "audio-viz":
      return <AudioVizScene audioSrc={scene.audioSrc || ""} variant={(scene.variant as "waveform" | "spectrum") || "waveform"} barCount={scene.barCount || 64} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    case "map-geo":
      return <MapScene centerLat={scene.centerLat ?? 0} centerLng={scene.centerLng ?? 0} zoom={scene.zoom ?? 5} style={(scene.style as "streets" | "satellite" | "dark") || "streets"} title={scene.title} markers={scene.markers || []} routes={scene.routes || []} duration={dur} wordTimestamps={ts} sceneStartFrame={sf} />;
    default:
      return (
        <AbsoluteFill style={{ background: colors.backgroundGradient, justifyContent: "center", alignItems: "center", color: colors.text, fontFamily: fonts.heading, fontSize: 32 }}>
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
    return <AbsoluteFill style={{ background: colors.background }} />;
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
    <AbsoluteFill style={{ background: colors.background }}>
      {sceneElements}
      {audioElements}
      {captionElements}
    </AbsoluteFill>
  );
};
