import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { colors, fonts } from "../../design-tokens";

export const KineticTextSceneSchema = z.object({
  type: z.literal("kinetic"),
  lines: z
    .array(
      z.object({
        text: z.string(),
        highlightWords: z.array(z.string()).optional(),
        animation: z
          .enum(["fade", "slide", "scale", "bounce"])
          .optional()
          .default("fade"),
      }),
    )
    .min(1),
  lineAnimation: z
    .enum(["sequential", "simultaneous"])
    .optional()
    .default("sequential"),
  duration: z.number().positive(),
  wordTimestamps: z
    .array(
      z.object({ text: z.string(), startMs: z.number(), endMs: z.number() }),
    )
    .optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type KineticTextSceneProps = z.infer<typeof KineticTextSceneSchema>;

const WORD_STAGGER = 8;
const WORD_DURATION = 15;
const HIGHLIGHT_SCALE_PEAK = 1.08;
const PULSE_CYCLE = 40;

interface WordInfo {
  text: string;
  clean: string;
  globalIdx: number;
}

interface LineWords {
  text: string;
  words: WordInfo[];
  highlightWords: string[];
  animation: string;
}

function getAnimationStyle(
  wordFrame: number,
  anim: string,
  fps: number,
): { opacity: number; transform: string } {
  const clamped = Math.max(0, wordFrame);
  const progress = interpolate(clamped, [0, WORD_DURATION], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  switch (anim) {
    case "fade":
      return { opacity: progress, transform: "translateY(0)" };
    case "slide":
      return {
        opacity: progress,
        transform: `translateY(${interpolate(progress, [0, 1], [30, 0])}px)`,
      };
    case "scale":
      return {
        opacity: progress,
        transform: `scale(${interpolate(progress, [0, 1], [0.8, 1.0])})`,
      };
    case "bounce": {
      const s = spring({
        frame: clamped,
        fps,
        config: { damping: 10, stiffness: 120 },
      });
      return {
        opacity: s,
        transform: `scale(${interpolate(s, [0, 1], [0.5, 1.0])})`,
      };
    }
    default:
      return { opacity: progress, transform: "translateY(0)" };
  }
}

function getHighlightPulse(frame: number, wordStartFrame: number): number {
  const elapsed = Math.max(0, frame - wordStartFrame - WORD_DURATION);
  if (elapsed <= 0) return 1;
  return interpolate(
    elapsed % PULSE_CYCLE,
    [0, PULSE_CYCLE * 0.25, PULSE_CYCLE * 0.5, PULSE_CYCLE],
    [1, HIGHLIGHT_SCALE_PEAK, 1, HIGHLIGHT_SCALE_PEAK],
    { extrapolateLeft: "clamp", extrapolateRight: "cycle" },
  );
}

export const KineticTextScene: React.FC<KineticTextSceneProps> = ({
  lines,
  lineAnimation = "sequential",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lineWords: LineWords[] = useMemo(() => {
    let idx = 0;
    return lines.map((l) => ({
      text: l.text,
      highlightWords: l.highlightWords ?? [],
      animation: l.animation ?? "fade",
      words: l.text
        .split(/\s+/)
        .filter(Boolean)
        .map((w) => {
          const clean = w.replace(/[^\w]/g, "");
          return { text: w, clean, globalIdx: idx++ };
        }),
    }));
  }, [lines]);

  const totalWords = lineWords.reduce((s, l) => s + l.words.length, 0);

  return (
    <AbsoluteFill
      style={{
        background: colors.backgroundGradient,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "60px 80px",
      }}
    >
      {lineWords.map((line, li) => {
        const firstGlobalIdx = line.words[0]?.globalIdx ?? 0;
        return (
          <div
            key={li}
            style={{
              display: "flex",
              flexWrap: "wrap",
              justifyContent: "center",
              gap: "0 14px",
              marginBottom: Math.max(16, 28 - li * 2),
              lineHeight: 1.5,
              maxWidth: "90%",
            }}
          >
            {line.words.map((word, wi) => {
              const wordStartFrame =
                lineAnimation === "sequential"
                  ? word.globalIdx * WORD_STAGGER
                  : wi * WORD_STAGGER;
              const wordFrame = frame - wordStartFrame;
              const isVisible = wordFrame >= 0;

              const { opacity, transform } = getAnimationStyle(
                wordFrame,
                line.animation,
                fps,
              );

              const isHighlighted = line.highlightWords.includes(word.clean);
              const pulse = isHighlighted
                ? getHighlightPulse(frame, wordStartFrame)
                : 1;

              const highlightOpacity = isHighlighted
                ? interpolate(
                    Math.max(0, wordFrame),
                    [0, 10],
                    [0.2, 0.15],
                    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
                  )
                : 0;

              return (
                <span
                  key={`${li}-${wi}`}
                  style={{
                    position: "relative",
                    fontFamily: fonts.heading,
                    fontSize: 42,
                    fontWeight: "700",
                    color: isHighlighted ? colors.primary : colors.text,
                    opacity: isVisible ? opacity : 0,
                    transform: isHighlighted
                      ? `${transform} scale(${pulse})`
                      : transform,
                    textShadow: isHighlighted
                      ? `0 0 24px ${colors.primary}50`
                      : "none",
                    display: "inline-block",
                    whiteSpace: "nowrap",
                    letterSpacing: "-0.3px",
                    transition: "none",
                  }}
                >
                  {isHighlighted && (
                    <span
                      style={{
                        position: "absolute",
                        inset: -4,
                        borderRadius: 6,
                        background: colors.primary,
                        opacity: highlightOpacity * opacity,
                        zIndex: -1,
                      }}
                    />
                  )}
                  {word.text}
                </span>
              );
            })}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
