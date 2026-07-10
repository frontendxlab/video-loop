import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, staticFile, interpolate } from "remotion";
import { useAudioData, visualizeAudio, visualizeAudioWaveform } from "@remotion/media-utils";
import { z } from "zod";
import { colors, fonts } from "../design-tokens";

export const AudioVizSceneSchema = z.object({
  audioSrc: z.string(),
  variant: z.enum(["waveform", "spectrum"]).default("waveform"),
  barCount: z.number().min(8).max(256).default(64),
  color: z.string().optional(),
  duration: z.number().positive(),
  wordTimestamps: z
    .array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() }))
    .optional(),
  sceneStartFrame: z.number().default(0),
});

export type AudioVizSceneProps = z.infer<typeof AudioVizSceneSchema>;

const MAX_BAR_WIDTH = 12;
const MIN_HEIGHT_PCT = 0.5;
const MAX_HEIGHT_PCT = 92;

export function getBarHeight(value: number, variant: "waveform" | "spectrum"): number {
  const raw = variant === "waveform" ? Math.abs(value) : Math.max(value, 0);
  return MIN_HEIGHT_PCT + raw * (MAX_HEIGHT_PCT - MIN_HEIGHT_PCT);
}

export const AudioVizScene: React.FC<AudioVizSceneProps> = ({
  audioSrc,
  variant = "waveform",
  barCount = 64,
  color,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const audioData = useAudioData(staticFile(audioSrc));

  const vizColor = color || colors.primary;

  let values: number[];
  if (!audioData) {
    values = new Array(barCount).fill(0);
  } else if (variant === "spectrum") {
    values = visualizeAudio({
      audioData,
      frame,
      fps,
      numberOfSamples: barCount,
      smoothing: true,
    });
  } else {
    values = visualizeAudioWaveform({
      audioData,
      frame,
      fps,
      windowInSeconds: duration / fps,
      numberOfSamples: barCount,
      normalize: true,
    });
  }

  const fadeIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });

  const containerStyle: React.CSSProperties = {
    position: "absolute",
    inset: 0,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    background: colors.backgroundGradient,
    opacity: fadeIn,
    padding: 40,
  };

  const barsGap = variant === "spectrum" ? 1 : 2;

  return (
    <AbsoluteFill style={containerStyle}>
      <div
        style={{
          display: "flex",
          alignItems: variant === "waveform" ? "center" : "flex-end",
          justifyContent: "center",
          width: "100%",
          flex: 1,
          gap: barsGap,
        }}
      >
        {values.map((value, i) => {
          const heightPct = getBarHeight(value, variant);
          const barOpacity =
            variant === "waveform"
              ? Math.max(0.25, Math.abs(value))
              : Math.max(0.35, value);

          const barStyle: React.CSSProperties = {
            width: `${100 / barCount}%`,
            maxWidth: MAX_BAR_WIDTH,
            height: `${heightPct}%`,
            backgroundColor: vizColor,
            borderRadius: variant === "spectrum" ? "3px 3px 0 0" : "3px",
            opacity: barOpacity,
            flexShrink: 0,
          };

          return <div key={i} style={barStyle} />;
        })}
      </div>
      <div
        style={{
          fontFamily: fonts.sans,
          fontSize: 13,
          color: colors.textMuted,
          letterSpacing: 3,
          textTransform: "uppercase",
          marginTop: 24,
          opacity: fadeIn,
        }}
      >
        {variant === "spectrum" ? "Frequency Spectrum" : "Audio Waveform"}
      </div>
    </AbsoluteFill>
  );
};
