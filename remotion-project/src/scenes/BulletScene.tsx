import React from "react";
import { AbsoluteFill, useCurrentFrame, spring, useVideoConfig, interpolate, Easing } from "remotion";
import { z } from "zod";

export const BulletSceneSchema = z.object({
  points: z.array(z.string()).min(1).max(8),
  title: z.string().optional(),
  entry: z.enum(["fadeIn", "slideIn", "scaleIn"]).optional().default("fadeIn"),
  duration: z.number().positive(),
});

export type BulletSceneProps = z.infer<typeof BulletSceneSchema>;

const STAGGER = 25;

export const BulletScene: React.FC<BulletSceneProps> = ({ points, title, entry = "fadeIn" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const titleOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });

  const calcSpring = (itemFrame: number) => spring({ frame: itemFrame, fps, config: { damping: 14, stiffness: 90 } });

  return (
    <AbsoluteFill style={{
      padding: 60, display: "flex", flexDirection: "column", justifyContent: "center",
      background: "linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%)",
    }}>
      {title && (
        <div style={{
          opacity: titleOpacity, marginBottom: 40,
          fontSize: 28, fontWeight: "700", color: "rgba(255,255,255,0.9)",
          letterSpacing: "-0.3px",
        }}>
          {title}
        </div>
      )}
      {points.map((point, i) => {
        const itemDelay = i * STAGGER;
        const itemFrame = frame - itemDelay;
        if (itemFrame < 0) return null;
        const s = calcSpring(itemFrame);
        const opacity = interpolate(itemFrame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
        const isActive = itemFrame < STAGGER + 10;
        const isDimmed = i < Math.floor(frame / STAGGER) && !isActive;

        const cardStyle: React.CSSProperties = {
          display: "flex", alignItems: "center",
          padding: "18px 24px",
          marginBottom: 12,
          borderRadius: 16,
          background: isActive ? "rgba(74, 144, 217, 0.12)" : "rgba(255,255,255,0.04)",
          border: `1px solid ${isActive ? "rgba(74,144,217,0.3)" : "rgba(255,255,255,0.06)"}`,
          backdropFilter: "blur(2px)",
          transform: `translateX(${(1 - s) * 30}px) scale(${0.95 + 0.05 * s})`,
          opacity: isDimmed ? 0.4 : opacity,
        };

        const bulletDot: React.CSSProperties = {
          width: 10, height: 10,
          borderRadius: "50%",
          background: isActive ? "#4a90d9" : isDimmed ? "#555" : "rgba(74,144,217,0.5)",
          marginRight: 16,
          flexShrink: 0,
          boxShadow: isActive ? "0 0 12px rgba(74,144,217,0.5)" : "none",
        };

        return (
          <div key={i} style={cardStyle}>
            <div style={bulletDot} />
            <span style={{
              fontSize: 20, color: isActive ? "#fff" : isDimmed ? "#666" : "rgba(255,255,255,0.8)",
              fontWeight: isActive ? "600" : "400",
            }}>
              {point}
            </span>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
