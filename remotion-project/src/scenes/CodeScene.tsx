import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { z } from "zod";

export const CodeSceneSchema = z.object({
  code: z.string(),
  lang: z.string().optional().default("text"),
  highlightLines: z.array(z.number()).optional().default([]),
  title: z.string().optional(),
  caption: z.string().optional(),
  duration: z.number().positive(),
});

export type CodeSceneProps = z.infer<typeof CodeSceneSchema>;

export const CodeScene: React.FC<CodeSceneProps> = ({ code, lang, highlightLines = [], title, caption }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const slideUp = spring({ frame, fps, config: { damping: 14, stiffness: 90 } });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const captionOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });

  const lines = code.split("\n");

  return (
    <AbsoluteFill style={{
      padding: 40, display: "flex", flexDirection: "column",
      background: "linear-gradient(135deg, #0d1117 0%, #161b22 100%)",
      opacity, transform: `translateY(${(1 - slideUp) * 20}px)`,
    }}>
      {title && (
        <div style={{
          opacity: titleOpacity, marginBottom: 16,
          fontSize: 22, fontWeight: "600", color: "rgba(255,255,255,0.9)",
        }}>
          {title}
        </div>
      )}
      <div style={{
        flex: 1, borderRadius: 16, overflow: "hidden",
        background: "#161b22",
        border: "1px solid rgba(255,255,255,0.06)",
        boxShadow: "none",
      }}>
        <div style={{
          padding: "12px 16px", background: "rgba(255,255,255,0.03)",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#ff5f57" }} />
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#ffbd2e" }} />
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#28c840" }} />
          <span style={{ marginLeft: 12, fontSize: 13, color: "rgba(255,255,255,0.4)" }}>{lang}</span>
        </div>
        <div style={{ padding: 16, fontFamily: "monospace", fontSize: 16, lineHeight: "1.6", overflow: "auto" }}>
          {lines.map((line, i) => {
            const isHighlighted = highlightLines.includes(i + 1);
            const lineDelay = i * 2;
            const lineOpacity = Math.min(1, Math.max(0, (frame - lineDelay) / 10));
            return (
              <div key={i} style={{
                display: "flex",
                opacity: lineOpacity,
                background: isHighlighted ? "rgba(74,144,217,0.12)" : "transparent",
                borderRadius: 4, padding: "1px 0",
                borderLeft: isHighlighted ? "3px solid #4a90d9" : "3px solid transparent",
              }}>
                <span style={{ width: 36, color: "rgba(255,255,255,0.3)", textAlign: "right", marginRight: 16, flexShrink: 0, fontSize: 14 }}>
                  {i + 1}
                </span>
                <span style={{ color: isHighlighted ? "#fff" : "rgba(255,255,255,0.75)", whiteSpace: "pre" }}>
                  {line || " "}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      {caption && (
        <div style={{
          opacity: captionOpacity, marginTop: 12,
          fontSize: 16, color: "rgba(255,255,255,0.5)", textAlign: "center",
        }}>
          {caption}
        </div>
      )}
    </AbsoluteFill>
  );
};
