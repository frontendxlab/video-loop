import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { colors, fonts, spacing } from "../design-tokens";

export const LowerThirdSchema = z.object({
  title: z.string().min(1),
  subtitle: z.string().optional(),
  duration: z.number().positive(),
  slideDirection: z.enum(["left", "up"]).optional().default("left"),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type LowerThirdProps = z.infer<typeof LowerThirdSchema>;

export const LowerThird: React.FC<LowerThirdProps> = ({
  title, subtitle, slideDirection = "left", wordTimestamps, sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const localFrame = frame - sceneStartFrame;
  const animDuration = Math.min(20, Math.floor((wordTimestamps?.[0]?.endMs ?? 500) / (1000 / fps)));

  const entryProgress = interpolate(localFrame, [0, animDuration], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });
  const holdOpacity = interpolate(localFrame, [animDuration, localFrame], [1, 1], {
    extrapolateRight: "clamp",
  });
  const subtitleOpacity = interpolate(localFrame, [10, 10 + animDuration], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });

  const slideSpring = spring({
    frame: Math.min(localFrame, animDuration),
    fps, config: { damping: 14, stiffness: 100 },
  });

  const translateX = slideDirection === "left"
    ? interpolate(slideSpring, [0, 1], [-120, 0])
    : 0;
  const translateY = slideDirection === "up"
    ? interpolate(slideSpring, [0, 1], [60, 0])
    : 0;

  return (
    <AbsoluteFill style={{ background: "transparent" }}>
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: slideDirection === "left" ? 60 : "50%",
          transform: slideDirection === "left"
            ? `translateX(${translateX}px)`
            : `translateX(-50%) translateY(${translateY}px)`,
          opacity: Math.min(entryProgress, holdOpacity),
          display: "flex",
          flexDirection: "column",
          alignItems: slideDirection === "left" ? "flex-start" : "center",
        }}
      >
        <div
          style={{
            background: colors.chromePanel,
            backdropFilter: "blur(12px)",
            borderRadius: 16,
            padding: `${spacing.md}px ${spacing.lg}px`,
            border: `1px solid ${colors.chromeBorder}`,
            boxShadow: `0 4px 24px rgba(0,0,0,0.3)`,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: spacing.sm,
            }}
          >
            <div
              style={{
                width: 4,
                height: 28,
                borderRadius: 2,
                background: `linear-gradient(180deg, ${colors.primary}, ${colors.secondary})`,
                flexShrink: 0,
              }}
            />
            <div>
              <span
                style={{
                  fontFamily: fonts.heading,
                  fontSize: 28,
                  fontWeight: "700",
                  color: colors.text,
                  letterSpacing: "-0.3px",
                  lineHeight: 1.2,
                }}
              >
                {title}
              </span>
              {subtitle && (
                <div
                  style={{
                    opacity: subtitleOpacity,
                    marginTop: 4,
                  }}
                >
                  <span
                    style={{
                      fontFamily: fonts.sans,
                      fontSize: 16,
                      fontWeight: "400",
                      color: colors.textMuted,
                      letterSpacing: "0.3px",
                    }}
                  >
                    {subtitle}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
