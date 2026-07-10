import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render } from "@testing-library/react";
import { PathDraw } from "../../src/components/primitives/PathDraw";

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

describe("PathDraw", () => {
  beforeEach(() => {
    mockState.frame = 0;
  });

  it("renders a path element with d attribute", () => {
    const { container } = render(
      <svg>
        <PathDraw d="M 0 0 L 100 100" durationInFrames={30} />
      </svg>,
    );
    const path = container.querySelector("path");
    expect(path).toBeTruthy();
    expect(path!.getAttribute("d")).toBe("M 0 0 L 100 100");
  });

  it("has stroke-dasharray attribute", () => {
    const { container } = render(
      <svg>
        <PathDraw d="M 0 0 L 100 0" durationInFrames={30} />
      </svg>,
    );
    const path = container.querySelector("path");
    expect(Number(path!.getAttribute("stroke-dasharray"))).toBeGreaterThan(0);
    expect(Number(path!.getAttribute("stroke-dashoffset"))).toBeGreaterThan(0);
  });

  it("applies custom stroke color", () => {
    const { container } = render(
      <svg>
        <PathDraw d="M 0 0 L 10 10" durationInFrames={30} stroke="#FF0000" />
      </svg>,
    );
    expect(container.querySelector("path")!.getAttribute("stroke")).toBe("#FF0000");
  });

  it("dashoffset decreases as frame advances", () => {
    const { container: c0 } = render(
      <svg>
        <PathDraw d="M 0 0 L 100 0" durationInFrames={30} />
      </svg>,
    );
    const offset0 = Number(c0.querySelector("path")!.getAttribute("stroke-dashoffset"));

    mockState.frame = 15;
    const { container: c15 } = render(
      <svg>
        <PathDraw d="M 0 0 L 100 0" durationInFrames={30} />
      </svg>,
    );
    const offset15 = Number(c15.querySelector("path")!.getAttribute("stroke-dashoffset"));

    expect(offset15).toBeLessThan(offset0);
  });
});
