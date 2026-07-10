import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { WordTiming, frameToMs, getCurrentWordIndex, getWordOpacity } from "./wordTiming";
import { colors, fonts, spacing } from "../design-tokens";

interface CaptionBarProps {
  words: WordTiming[];
  fps?: number;
  /** Gradient accent color bar on the left. Defaults to colors.primary. */
  accentColor?: string;
  /** Bottom offset in px. Defaults to 80. */
  bottomOffset?: number;
}

export const CaptionBar: React.FC<CaptionBarProps> = ({
  words,
  fps = 30,
  accentColor = colors.primary,
  bottomOffset = 80,
}) => {
  const frame = useCurrentFrame();
  const { fps: compFps } = useVideoConfig();
  const effectiveFps = fps ?? compFps;
  const currentMs = frameToMs(frame, effectiveFps);
  const currentWordIndex = getCurrentWordIndex(words, currentMs);

  if (words.length === 0) return null;

  const progress =
    currentWordIndex >= 0
      ? (currentWordIndex + 1) / words.length
      : currentMs > words[words.length - 1]?.endMs
        ? 1
        : 0;

  const animDuration = 15;
  const entryProgress = interpolate(frame, [0, animDuration], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const slideSpring = spring({
    frame: Math.min(frame, animDuration),
    fps: effectiveFps,
    config: { damping: 14, stiffness: 100 },
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomOffset,
        left: "50%",
        transform: `translateX(-50%) translateY(${interpolate(slideSpring, [0, 1], [20, 0])}px)`,
        zIndex: 100,
        maxWidth: "80%",
        minWidth: 320,
        opacity: entryProgress,
      }}
    >
      <div
        style={{
          display: "flex",
          background: colors.chromePanel,
          backdropFilter: "blur(12px)",
          borderRadius: 12,
          border: `1px solid ${colors.chromeBorder}`,
          boxShadow: `0 4px 24px rgba(0,0,0,0.3)`,
          overflow: "hidden",
        }}
      >
        {/* Gradient accent bar */}
        <div
          style={{
            width: 4,
            background: `linear-gradient(180deg, ${accentColor}, ${colors.secondary})`,
            flexShrink: 0,
          }}
        />

        {/* Caption word row */}
        <div
          style={{
            flex: 1,
            padding: `${spacing.md}px ${spacing.lg}px`,
            display: "flex",
            flexWrap: "wrap",
            gap: "4px 8px",
            alignItems: "center",
          }}
        >
          {words.map((word, i) => {
            const opacity = getWordOpacity(i, currentWordIndex);
            const isCurrent = i === currentWordIndex;

            return (
              <span
                key={i}
                style={{
                  fontFamily: fonts.sans,
                  fontSize: 22,
                  fontWeight: isCurrent ? 600 : 400,
                  color: isCurrent ? colors.highlight : colors.text,
                  opacity,
                  textShadow: "0 1px 3px rgba(0,0,0,0.4)",
                  transition: "opacity 0.15s, color 0.15s, font-weight 0.15s",
                }}
              >
                {word.text}
              </span>
            );
          })}
        </div>
      </div>

      {/* Progress bar */}
      <div
        style={{
          marginTop: 8,
          height: 3,
          borderRadius: 2,
          background: colors.chromeBorder,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress * 100}%`,
            background: `linear-gradient(90deg, ${accentColor}, ${colors.secondary})`,
            borderRadius: 2,
            transition: "width 0.1s linear",
          }}
        />
      </div>
    </div>
  );
};
