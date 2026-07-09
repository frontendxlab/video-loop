import React from "react";
import { useCurrentFrame } from "remotion";
import { WordTiming, frameToMs, getCurrentWordIndex, getWordOpacity } from "./wordTiming";
import { colors } from "../design-tokens";

interface CaptionOverlayProps {
  words: WordTiming[];
  fps?: number;
}

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  words,
  fps = 30,
}) => {
  const frame = useCurrentFrame();
  const currentMs = frameToMs(frame, fps);
  const currentWordIndex = getCurrentWordIndex(words, currentMs);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 100,
        padding: "0 40px",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "4px 8px",
          backgroundColor: "rgba(0, 0, 0, 0.6)",
          borderRadius: 12,
          padding: "12px 24px",
          maxWidth: "80%",
        }}
      >
        {words.map((word, i) => {
          const opacity = getWordOpacity(i, currentWordIndex);
          const isCurrent = i === currentWordIndex;

          return (
            <span
              key={i}
              style={{
                fontSize: 24,
                color: isCurrent ? colors.highlight : colors.text,
                opacity,
                transition: "opacity 0.15s, color 0.15s",
                textShadow: "0 1px 2px rgba(0,0,0,0.5)",
              }}
            >
              {word.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};
