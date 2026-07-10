import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { colors, fonts, spacing } from "../design-tokens";

export const OverlayCTASchema = z.object({
  title: z.string().min(1),
  subtitle: z.string().optional(),
  cta: z.string().optional(),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type OverlayCTAProps = z.infer<typeof OverlayCTASchema>;

export const OverlayCTA: React.FC<OverlayCTAProps> = ({
  title, subtitle, cta, wordTimestamps, sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const localFrame = frame - sceneStartFrame;
  const fadeDuration = Math.min(25, Math.floor((wordTimestamps?.[0]?.endMs ?? 500) / (1000 / fps)));

  const backdropOpacity = interpolate(localFrame, [0, fadeDuration], [0, 0.7], {
    extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });

  const contentSpring = spring({
    frame: Math.min(localFrame, fadeDuration),
    fps, config: { damping: 12, stiffness: 80 },
  });
  const contentOpacity = interpolate(localFrame, [0, fadeDuration], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });

  const ctaDelay = 8;
  const ctaOpacity = interpolate(localFrame - ctaDelay, [0, fadeDuration], [0, 1], {
    extrapolateRight: "clamp",
  });
  const ctaSpring = spring({
    frame: Math.max(0, localFrame - ctaDelay),
    fps, config: { damping: 10, stiffness: 120 },
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: colors.black,
          opacity: backdropOpacity,
        }}
      />
      <div
        style={{
          opacity: contentOpacity,
          transform: `scale(${contentSpring})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          zIndex: 1,
        }}
      >
        <div
          style={{
            textAlign: "center",
            padding: `${spacing.xxl}px ${spacing.section}px`,
            background: colors.chromePanel,
            backdropFilter: "blur(12px)",
            borderRadius: 24,
            border: `1px solid ${colors.chromeBorder}`,
            boxShadow: `0 8px 32px rgba(0,0,0,0.4)`,
          }}
        >
          <span
            style={{
              fontFamily: fonts.heading,
              fontSize: 42,
              fontWeight: "700",
              color: colors.text,
              letterSpacing: "-0.5px",
              lineHeight: 1.2,
            }}
          >
            {title}
          </span>
          {subtitle && (
            <div style={{ marginTop: spacing.md }}>
              <span
                style={{
                  fontFamily: fonts.sans,
                  fontSize: 20,
                  color: colors.textMuted,
                  lineHeight: 1.4,
                }}
              >
                {subtitle}
              </span>
            </div>
          )}
          {subtitle && (
            <div
              style={{
                width: 60,
                height: 4,
                borderRadius: 2,
                background: `linear-gradient(90deg, ${colors.primary}, ${colors.secondary})`,
                margin: `${spacing.md}px auto`,
              }}
            />
          )}
        </div>

        {cta && (
          <div
            style={{
              opacity: ctaOpacity,
              marginTop: 32,
              transform: `scale(${ctaSpring})`,
            }}
          >
            <div
              style={{
                padding: "16px 48px",
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})`,
                borderRadius: 12,
                boxShadow: `0 4px 16px ${colors.primary}40`,
                cursor: "pointer",
              }}
            >
              <span
                style={{
                  color: colors.white,
                  fontSize: 20,
                  fontWeight: "600",
                  letterSpacing: "0.5px",
                  fontFamily: fonts.sans,
                }}
              >
                {cta}
              </span>
            </div>
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
