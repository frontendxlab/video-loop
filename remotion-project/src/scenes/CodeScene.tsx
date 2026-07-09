import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { WordTiming } from "../captions/wordTiming";
import { getStepProgress } from "../timing/audio-timing";
import { ShikiCode } from "../components/ShikiCode";

export const CodeSceneSchema = z.object({
  code: z.string(),
  lang: z.string().optional().default("text"),
  highlightLines: z.array(z.number()).optional().default([]),
  title: z.string().optional(),
  caption: z.string().optional(),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type CodeSceneProps = z.infer<typeof CodeSceneSchema>;

export const CodeScene: React.FC<CodeSceneProps> = ({ code, lang, highlightLines = [], title, caption, wordTimestamps, sceneStartFrame = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const slideUp = spring({ frame, fps, config: { damping: 14, stiffness: 90 } });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });
  const captionOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });

  const lines = code.split("\n");
  const totalWords = wordTimestamps?.length ?? 0;
  const visibleLines = (() => {
    if (!wordTimestamps || totalWords === 0) {
      return Math.min(lines.length, Math.max(1, Math.floor((frame / 10) + 1)));
    }
    const wordsPerLine = totalWords / lines.length;
    const currentWordIdx = wordTimestamps.findIndex(
      (w) => ((frame - sceneStartFrame) / fps) * 1000 < w.startMs,
    );
    const activeWord = currentWordIdx === -1 ? totalWords : currentWordIdx;
    return Math.min(lines.length, Math.max(1, Math.ceil(activeWord / wordsPerLine)));
  })();

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
        <div style={{ padding: 16, overflow: "auto" }}>
          <ShikiCode
            code={code}
            lang={lang || "text"}
            theme="poimandres"
            highlightLines={highlightLines}
            visibleLines={visibleLines}
          />
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
