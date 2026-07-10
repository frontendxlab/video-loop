import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import { getDrawPathProps, estimatePathLength } from "./path-utils";

interface PathDrawProps {
  /** SVG path `d` attribute */
  d: string;
  /** Duration of draw animation in frames */
  durationInFrames: number;
  /** Delay before draw starts (frames) */
  delay?: number;
  /** Stroke color */
  stroke?: string;
  /** Stroke width */
  strokeWidth?: number;
  /** Fill */
  fill?: string;
  /** Line cap */
  strokeLinecap?: "round" | "butt" | "square";
  /** Opacity */
  opacity?: number;
  /** Wrapper <g> props or transform */
  transform?: string;
  /** Custom path length override (avoids estimation) */
  pathLength?: number;
}

export const PathDraw: React.FC<PathDrawProps> = ({
  d,
  durationInFrames,
  delay = 0,
  stroke = "currentColor",
  strokeWidth = 3,
  fill = "none",
  strokeLinecap = "round",
  opacity = 1,
  transform,
  pathLength: overrideLength,
}) => {
  const frame = useCurrentFrame();

  const len = useMemo(
    () => overrideLength ?? estimatePathLength(d),
    [d, overrideLength],
  );

  const { strokeDasharray, strokeDashoffset } = getDrawPathProps(
    frame,
    durationInFrames,
    len,
    { delay },
  );

  return (
    <path
      d={d}
      fill={fill}
      stroke={stroke}
      strokeWidth={strokeWidth}
      strokeLinecap={strokeLinecap}
      strokeDasharray={strokeDasharray}
      strokeDashoffset={strokeDashoffset}
      opacity={opacity}
      transform={transform}
    />
  );
};
