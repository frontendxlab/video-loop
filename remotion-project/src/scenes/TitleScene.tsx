import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { z } from "zod";

export const TitleSceneSchema = z.object({
  title: z.string(),
  subtitle: z.string().optional(),
  duration: z.number().positive(),
  animation: z.enum(["fadeIn", "slideUp", "typewriter"]).optional().default("fadeIn"),
});

export type TitleSceneProps = z.infer<typeof TitleSceneSchema>;

export const TitleScene: React.FC<TitleSceneProps> = ({
  title, subtitle, animation = "fadeIn",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const springProgress = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });
  const fadeOpacity = interpolate(frame, [0, 40], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const slideY = interpolate(springProgress, [0, 1], [60, 0]);
  const subOpacity = interpolate(frame, [20, 50], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const charsPerFrame = title.length / 30;
  const typewritten = title.slice(0, Math.floor(frame * charsPerFrame));

  const cardStyle: React.CSSProperties = {
    position: "absolute", inset: 0,
    display: "flex", flexDirection: "column",
    alignItems: "center", justifyContent: "center",
    background: "linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #16213e 100%)",
  };

  const titleCardStyle: React.CSSProperties = {
    background: "rgba(255,255,255,0.06)",
    backdropFilter: "blur(2px)",
    borderRadius: 24,
    padding: "48px 64px",
    border: "1px solid rgba(255,255,255,0.08)",
    boxShadow: "none",
    transform: `translateY(${slideY}px)`,
    opacity: fadeOpacity,
  };

  const titleTextStyle: React.CSSProperties = {
    fontSize: 52,
    fontWeight: "700",
    color: "#fff",
    textAlign: "center",
    letterSpacing: "-0.5px",
    lineHeight: 1.2,
  };

  const accentStyle: React.CSSProperties = {
    width: 60,
    height: 4,
    borderRadius: 2,
    background: "linear-gradient(90deg, #4a90d9, #7c5cbf)",
    margin: "16px auto",
    transform: `scaleX(${springProgress})`,
  };

  const subtitleStyle: React.CSSProperties = {
    fontSize: 20,
    color: "rgba(255,255,255,0.6)",
    textAlign: "center",
    marginTop: 8,
    opacity: subOpacity,
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
