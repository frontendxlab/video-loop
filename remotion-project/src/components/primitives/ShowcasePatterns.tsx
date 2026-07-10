import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { SHOWCASE_PATTERNS, estimatePathLength } from "./path-utils";
import { PathDraw } from "./PathDraw";
import { colors } from "../../design-tokens";

interface PatternDef {
  patternKey: string;
  durationInFrames?: number;
  delay?: number;
  stroke?: string;
  strokeWidth?: number;
  fill?: string;
  transform?: string;
}

interface ShowcasePatternsProps {
  /** Which patterns to show. Empty = all. */
  patterns?: string[];
  /** Override per-pattern config */
  overrides?: PatternDef[];
  /** Duration per pattern reveal */
  perPatternDuration?: number;
  /** Stagger delay between patterns */
  staggerDelay?: number;
  /** Background color */
  background?: string;
  /** Show pattern labels */
  showLabels?: boolean;
}

const DEFAULT_PER_PATTERN = 30;
const DEFAULT_STAGGER = 8;

const patternKeys = Object.keys(SHOWCASE_PATTERNS);

export const ShowcasePatterns: React.FC<ShowcasePatternsProps> = ({
  patterns,
  overrides,
  perPatternDuration = DEFAULT_PER_PATTERN,
  staggerDelay = DEFAULT_STAGGER,
  background = colors.background,
  showLabels = false,
}) => {
  const keys = patterns ?? patternKeys;
  const overrideMap = new Map(
    (overrides ?? []).map((o) => [o.patternKey, o]),
  );

  return (
    <AbsoluteFill style={{ background, overflow: "hidden" }}>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {keys.map((key, i) => {
          const pattern = SHOWCASE_PATTERNS[key];
          if (!pattern) return null;
          const ov = overrideMap.get(key);
          const delay = ov?.delay ?? i * staggerDelay;
          const duration = ov?.durationInFrames ?? perPatternDuration;
          return (
            <PathDraw
              key={key}
              d={pattern.d}
              durationInFrames={duration}
              delay={delay}
              stroke={ov?.stroke ?? colors.primary}
              strokeWidth={ov?.strokeWidth ?? 3}
              fill={ov?.fill ?? "none"}
              transform={ov?.transform}
            />
          );
        })}
      </svg>
      {showLabels && (
        <div style={{ position: "absolute", bottom: 40, left: 0, right: 0, textAlign: "center" }}>
          {keys.map((key) => (
            <span
              key={key}
              style={{
                color: colors.textMuted,
                fontSize: 14,
                margin: "0 12px",
                fontFamily: "monospace",
              }}
            >
              {SHOWCASE_PATTERNS[key]?.label ?? key}
            </span>
          ))}
        </div>
      )}
    </AbsoluteFill>
  );
};
