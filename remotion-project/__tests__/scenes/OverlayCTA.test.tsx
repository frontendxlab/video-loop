/** OverlayCTA tests. */

import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import React from "react";

vi.mock("remotion", () => ({
  useCurrentFrame: () => 60,
  useVideoConfig: () => ({ fps: 30, width: 1920, height: 1080 }),
  interpolate: (_f: number, _in: number[], out: number[]) => out[out.length - 1] ?? 1,
  spring: () => 1,
  Easing: { out: () => (t: number) => t, cubic: {} },
  AbsoluteFill: ({ style, children }: any) => <div style={style}>{children}</div>,
}));

describe("OverlayCTA", () => {
  it("renders title text", async () => {
    const { OverlayCTA } = await import("../../src/scenes/OverlayCTA");
    const { container } = render(<OverlayCTA title="Get Started" duration={60} />);
    expect(container.textContent).toContain("Get Started");
  });

  it("renders CTA button text when provided", async () => {
    const { OverlayCTA } = await import("../../src/scenes/OverlayCTA");
    const { container } = render(
      <OverlayCTA title="Ready?" cta="Sign Up Now" duration={60} />,
    );
    expect(container.textContent).toContain("Sign Up Now");
  });

  it("renders subtitle when provided", async () => {
    const { OverlayCTA } = await import("../../src/scenes/OverlayCTA");
    const { container } = render(
      <OverlayCTA title="Ready?" subtitle="Start your free trial" duration={60} />,
    );
    expect(container.textContent).toContain("Start your free trial");
  });

  it("rejects empty title", async () => {
    const { OverlayCTASchema } = await import("../../src/scenes/OverlayCTA");
    expect(() => OverlayCTASchema.parse({ title: "", duration: 60 })).toThrow();
  });
});
