import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame } from "remotion";
import { CaptionOverlay } from "../captions/CaptionOverlay";
import { TitleScene } from "../scenes/TitleScene";
import { CodeScene } from "../scenes/CodeScene";
import { BulletScene } from "../scenes/BulletScene";
import { ImageScene } from "../scenes/ImageScene";
import { OutroScene } from "../scenes/OutroScene";

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
  duration: number;
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

const renderScene = (scene: SceneData) => {
  const dur = scene.duration;
  switch (scene.type) {
    case "title":
      return <TitleScene title={scene.title || ""} subtitle={scene.subtitle} duration={dur} />;
    case "code":
      return <CodeScene code={scene.code || ""} lang={scene.lang || "text"} highlightLines={[]} caption={scene.caption} duration={dur} />;
    case "bullet":
      return <BulletScene points={scene.points || []} duration={dur} />;
    case "image":
      return <ImageScene src={scene.src || ""} caption={scene.caption} duration={dur} />;
    case "outro":
      return <OutroScene title={scene.title || "Thank You"} cta={scene.cta} duration={dur} />;
    default:
      return (
        <AbsoluteFill style={{ backgroundColor: "#1a1a2e", justifyContent: "center", alignItems: "center", color: "white", fontSize: 32 }}>
          {scene.title || scene.caption || ""}
        </AbsoluteFill>
      );
  }
};

export const VideoComposition: React.FC<VideoCompositionProps> = ({ scenes, audioTracks, captions }) => {
  if (!scenes || scenes.length === 0) {
    return <AbsoluteFill style={{ backgroundColor: "#000" }} />;
  }

  let frameOffset = 0;
  const elements: React.ReactNode[] = [];

  for (let i = 0; i < scenes.length; i++) {
    const scene = scenes[i];
    const dur = scene.duration;
    elements.push(
      <Sequence key={`scene-${i}`} from={frameOffset} durationInFrames={dur}>
        {renderScene(scene)}
      </Sequence>
    );
    frameOffset += dur;
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f0f23" }}>
      {elements}
      {audioTracks.map((track, i) => (
        <Audio key={`audio-${i}`} src={staticFile(track.src)} startFrom={track.startFrame} endAt={track.startFrame + track.durationFrames} />
      ))}
      {captions.length > 0 && <CaptionOverlay words={captions} fps={30} />}
    </AbsoluteFill>
  );
};
