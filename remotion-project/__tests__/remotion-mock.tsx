import React from "react";

/**
 * Shared mutable frame state for tests.
 * Set via <RemotionMock frame={N}> before rendering components that use useCurrentFrame().
 */

let _currentFrame = 0;

export function __setMockFrame(f: number) {
  _currentFrame = f;
}

/* ─── Remotion hook/component mocks ─── */

export const useCurrentFrame = () => _currentFrame;

export const useVideoConfig = () => ({
  width: 1920,
  height: 1080,
  fps: 30,
  durationInFrames: 300,
});

export function interpolate(
  frame: number,
  inputRange: [number, number],
  outputRange: [number, number],
  opts?: { extrapolateLeft?: string; extrapolateRight?: string; easing?: (t: number) => number },
): number {
  const t = (frame - inputRange[0]) / (inputRange[1] - inputRange[0]);
  const clampMin = opts?.extrapolateLeft === "clamp" ? Math.max(0, t) : t;
  const clamped = opts?.extrapolateRight === "clamp" ? Math.min(1, clampMin) : clampMin;
  const eased = opts?.easing ? opts.easing(clamped) : clamped;
  return outputRange[0] + (outputRange[1] - outputRange[0]) * eased;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const _dummy = (t: number) => t;

export const Easing = {
  out: () => (t: number) => t,
  inOut: () => (t: number) => t,
  cubic: {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    out: (_dummy?: any) => (t: number) => t,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    inOut: (_dummy?: any) => (t: number) => t,
  },
};

export const spring = ({
  frame: f,
  fps = 30,
}: {
  frame: number;
  fps?: number;
  config?: Record<string, unknown>;
}) => Math.min(1, f / fps);

export const AbsoluteFill: React.FC<{
  children?: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ children, style }) => (
  <div
    style={{
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      ...style,
    }}
  >
    {children}
  </div>
);

/* ─── Test wrapper: sets _currentFrame for children ─── */

export const RemotionMock: React.FC<{
  frame: number;
  children: React.ReactNode;
}> = ({ frame, children }) => {
  _currentFrame = frame;
  return <>{children}</>;
};
