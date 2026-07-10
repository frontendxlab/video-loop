import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { interpolatePaths } from "./path-utils";

interface PathMorphProps {
  /** Starting SVG path `d` */
  from: string;
  /** Ending SVG path `d` */
  to: string;
  /** Duration of morph in frames */
  durationInFrames: number;
  /** Delay before morph starts */
  delay?: number;
  /** Stroke color */
  stroke?: string;
  /** Stroke width */
  strokeWidth?: number;
  /** Fill */
  fill?: string;
  /** Opacity */
  opacity?: number;
  /** Line cap */
  strokeLinecap?: "round" | "butt" | "square";
  /** Transform applied to <g> */
  transform?: string;
  /** Easing function override */
  easing?: (t: number) => number;
}

export const PathMorph: React.FC<PathMorphProps> = ({
  from,
  to,
  durationInFrames,
  delay = 0,
  stroke = "currentColor",
  strokeWidth = 3,
  fill = "none",
  opacity = 1,
  strokeLinecap = "round",
  transform,
  easing: easingFn = Easing.inOut(Easing.cubic),
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(frame, [delay, delay + durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easingFn,
  });

  const d = interpolatePaths(from, to, progress);

  return (
    <path
      d={d}
      fill={fill}
      stroke={stroke}
      strokeWidth={strokeWidth}
      strokeLinecap={strokeLinecap}
      opacity={opacity}
      transform={transform}
    />
  );
};
