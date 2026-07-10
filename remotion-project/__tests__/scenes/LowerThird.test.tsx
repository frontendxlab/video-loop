/** LowerThird tests. */

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

describe("LowerThird", () => {
  it("renders title text", async () => {
    const { LowerThird } = await import("../../src/scenes/LowerThird");
    const { container } = render(<LowerThird title="John Doe" duration={60} />);
    expect(container.textContent).toContain("John Doe");
  });

  it("renders subtitle when provided", async () => {
    const { LowerThird } = await import("../../src/scenes/LowerThird");
    const { container } = render(
      <LowerThird title="John Doe" subtitle="Software Engineer" duration={60} />,
    );
    expect(container.textContent).toContain("Software Engineer");
  });

  it("defaults to slideDirection=left", async () => {
    const { LowerThirdSchema } = await import("../../src/scenes/LowerThird");
    const parsed = LowerThirdSchema.parse({ title: "Test", duration: 60 });
    expect(parsed.slideDirection).toBe("left");
  });

  it("accepts slideDirection=up", async () => {
    const { LowerThirdSchema } = await import("../../src/scenes/LowerThird");
    const parsed = LowerThirdSchema.parse({
      title: "Test",
      duration: 60,
      slideDirection: "up",
    });
    expect(parsed.slideDirection).toBe("up");
  });

  it("rejects empty title", async () => {
    const { LowerThirdSchema } = await import("../../src/scenes/LowerThird");
    expect(() => LowerThirdSchema.parse({ title: "", duration: 60 })).toThrow();
  });
});
