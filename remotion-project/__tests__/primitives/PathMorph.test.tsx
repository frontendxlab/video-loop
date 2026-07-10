import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render } from "@testing-library/react";
import { PathMorph } from "../../src/components/primitives/PathMorph";

const mockState = vi.hoisted(() => ({ frame: 0 }));

vi.mock("remotion", () => ({
  useCurrentFrame: () => mockState.frame,
  useVideoConfig: () => ({ width: 1920, height: 1080, fps: 30, durationInFrames: 300 }),
  interpolate: (
    frame: number,
    inputRange: number[],
    outputRange: number[],
    opts?: { extrapolateLeft?: string; extrapolateRight?: string; easing?: (t: number) => number },
  ) => {
    const t = (frame - inputRange[0]) / (inputRange[1] - inputRange[0]);
    const clampMin = opts?.extrapolateLeft === "clamp" ? Math.max(0, t) : t;
    const clamped = opts?.extrapolateRight === "clamp" ? Math.min(1, clampMin) : clampMin;
    const eased = opts?.easing ? opts.easing(clamped) : clamped;
    return outputRange[0] + (outputRange[1] - outputRange[0]) * eased;
  },
  Easing: {
    inOut: () => (t: number) => t,
    cubic: { inOut: () => (t: number) => t },
  },
  spring: ({ frame: f }: { frame: number }) => Math.min(1, f / 30),
  AbsoluteFill: ({ children, style }: { children?: React.ReactNode; style?: React.CSSProperties }) =>
    React.createElement("div", { style: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, ...style } }, children),
}));

describe("PathMorph", () => {
  beforeEach(() => {
    mockState.frame = 0;
  });

  it("renders a path element", () => {
    const { container } = render(
      <svg>
        <PathMorph from="M 0 0 L 100 0" to="M 0 0 L 200 0" durationInFrames={30} />
      </svg>,
    );
    expect(container.querySelector("path")).toBeTruthy();
  });

  it("outputs from-path at frame 0", () => {
    const { container } = render(
      <svg>
        <PathMorph from="M 0 0 L 100 0" to="M 0 0 L 200 0" durationInFrames={30} />
      </svg>,
    );
    const d = container.querySelector("path")!.getAttribute("d");
    expect(d).toContain("100.0");
  });

  it("outputs to-path at end of duration", () => {
    mockState.frame = 30;
    const { container } = render(
      <svg>
        <PathMorph from="M 0 0 L 100 0" to="M 0 0 L 200 0" durationInFrames={30} />
      </svg>,
    );
    const d = container.querySelector("path")!.getAttribute("d");
    expect(d).toContain("200.0");
  });

  it("outputs interpolated midpoint at frame 15", () => {
    mockState.frame = 15;
    const { container } = render(
      <svg>
        <PathMorph from="M 0 0 L 100 0" to="M 0 0 L 200 0" durationInFrames={30} />
      </svg>,
    );
    const d = container.querySelector("path")!.getAttribute("d");
    expect(d).toContain("150.0");
  });

  it("applies custom stroke", () => {
    const { container } = render(
      <svg>
        <PathMorph from="M 0 0 L 10 10" to="M 0 0 L 20 20" durationInFrames={30} stroke="#00FF00" />
      </svg>,
    );
    expect(container.querySelector("path")!.getAttribute("stroke")).toBe("#00FF00");
  });
});
