import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { WordTiming } from "../captions/wordTiming";
import { getStepProgress } from "../timing/audio-timing";
import { colors, fonts } from "../design-tokens";

export const TitleSceneSchema = z.object({
  title: z.string(),
  subtitle: z.string().optional(),
  duration: z.number().positive(),
  animation: z.enum(["fadeIn", "slideUp", "typewriter"]).optional().default("fadeIn"),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type TitleSceneProps = z.infer<typeof TitleSceneSchema>;

export const TitleScene: React.FC<TitleSceneProps> = ({
  title, subtitle, animation = "fadeIn", wordTimestamps, sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  let titleProgress: number;
  let subProgress: number;

  if (wordTimestamps && wordTimestamps.length >= 4) {
    const titleStartMs = wordTimestamps[0].startMs;
    const titleEndMs = wordTimestamps[1].endMs;
    const subStartMs = wordTimestamps[2].startMs;
    const subEndMs = wordTimestamps[3].endMs;
    titleProgress = getStepProgress(frame, fps, titleStartMs, titleEndMs, sceneStartFrame);
    subProgress = getStepProgress(frame, fps, subStartMs, subEndMs, sceneStartFrame);
  } else if (wordTimestamps && wordTimestamps.length >= 2) {
    const titleStartMs = wordTimestamps[0].startMs;
    const titleEndMs = wordTimestamps[wordTimestamps.length - 1].endMs;
    titleProgress = getStepProgress(frame, fps, titleStartMs, titleEndMs, sceneStartFrame);
    subProgress = getStepProgress(frame, fps, titleStartMs, titleEndMs, sceneStartFrame);
  } else {
    titleProgress = interpolate(frame, [0, 40], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
    subProgress = interpolate(frame, [20, 50], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  }

  const springProgress = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });
  const slideY = interpolate(springProgress, [0, 1], [60, 0]);
  const charsPerFrame = title.length / 30;
  const typewritten = title.slice(0, Math.floor(frame * charsPerFrame));

  const cardStyle: React.CSSProperties = {
    position: "absolute", inset: 0,
    display: "flex", flexDirection: "column",
    alignItems: "center", justifyContent: "center",
    background: colors.backgroundGradient,
  };

  const titleCardStyle: React.CSSProperties = {
    background: colors.chromePanel,
    backdropFilter: "blur(2px)",
    borderRadius: 24,
    padding: "48px 64px",
    border: `1px solid ${colors.chromeBorder}`,
    boxShadow: "none",
    transform: `translateY(${slideY}px)`,
    opacity: titleProgress,
  };

  const titleTextStyle: React.CSSProperties = {
    fontFamily: fonts.heading,
    fontSize: 52,
    fontWeight: "700",
    color: colors.text,
    textAlign: "center",
    letterSpacing: "-0.5px",
    lineHeight: 1.2,
  };

  const accentStyle: React.CSSProperties = {
    width: 60,
    height: 4,
    borderRadius: 2,
    background: `linear-gradient(90deg, ${colors.primary}, ${colors.secondary})`,
    margin: "16px auto",
    transform: `scaleX(${springProgress})`,
  };

  const subtitleStyle: React.CSSProperties = {
    fontFamily: fonts.sans,
    fontSize: 20,
    color: colors.textSubtle,
    textAlign: "center",
    marginTop: 8,
    opacity: subProgress,
    letterSpacing: 1,
  };

  return (
    <AbsoluteFill style={cardStyle}>
      <div style={titleCardStyle}>
        <div style={titleTextStyle}>
          {animation === "typewriter" ? typewritten : title}
        </div>
        <div style={accentStyle} />
        {subtitle && <div style={subtitleStyle}>{subtitle}</div>}
      </div>
    </AbsoluteFill>
  );
};
