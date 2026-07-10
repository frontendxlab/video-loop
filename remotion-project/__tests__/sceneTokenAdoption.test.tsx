/** Verify remaining scenes/components consume shared design tokens. */

import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import React from "react";

// Mock Remotion hooks so scenes render in jsdom
vi.mock("remotion", () => ({
  useCurrentFrame: () => 60,
  useVideoConfig: () => ({ fps: 30, width: 1920, height: 1080 }),
  interpolate: (_f: number, _in: number[], out: number[]) => out[out.length - 1] ?? 1,
  spring: () => 1,
  Easing: { out: () => (t: number) => t, cubic: {} },
  AbsoluteFill: ({ style, children }: any) => <div style={style}>{children}</div>,
  Sequence: ({ children }: any) => <>{children}</>,
  Audio: () => null,
}));

describe("scenes consume design tokens", () => {
  it("ComparisonScene: no hardcoded colors", async () => {
    const { ComparisonScene } = await import("../src/scenes/ComparisonScene");
    const { container } = render(
      <ComparisonScene labelBefore="Old" labelAfter="New" duration={30} />,
    );
    const html = container.innerHTML;
    expect(html).not.toContain("#1a1a2e");
    expect(html).not.toContain("#16213e");
    expect(html).not.toContain("#ffeb3b");
    expect(html).not.toContain("#0f3460");
  });

  it("DiagramScene: no hardcoded colors", async () => {
    const { DiagramScene } = await import("../src/scenes/DiagramScene");
    const { container } = render(
      <DiagramScene
        config={{ nodes: [{ id: "1", label: "Test", position: { row: 0, col: 0 } }] }}
        duration={30}
      />,
    );
    expect(container.innerHTML).not.toContain("#1a1a2e");
  });

  it("ImageScene: no hardcoded colors", async () => {
    const { ImageScene } = await import("../src/scenes/ImageScene");
    const { container } = render(<ImageScene src="test.jpg" duration={30} />);
    expect(container.innerHTML).not.toContain("#0d1117");
    expect(container.innerHTML).not.toContain("#c9d1d9");
  });

  it("OutroScene: no hardcoded colors", async () => {
    const { OutroScene } = await import("../src/scenes/OutroScene");
    const { container } = render(<OutroScene title="Thanks" duration={60} />);
    const html = container.innerHTML;
    expect(html).not.toContain("#0f0f23");
    expect(html).not.toContain("#1a1a3e");
    expect(html).not.toContain("#7c5cbf");
  });

  it("ChartScene: no hardcoded colors", async () => {
    const { ChartScene } = await import("../src/components/scenes/ChartScene");
    const { container } = render(
      <ChartScene data={[{ label: "A", value: 10 }]} duration={60} />,
    );
    const html = container.innerHTML;
    expect(html).not.toContain("#0f0f23");
    expect(html).not.toContain("#1a1a3e");
    expect(html).not.toContain("#4a90d9");
  });

  it("TimelineScene: no hardcoded colors", async () => {
    const { TimelineScene } = await import("../src/components/scenes/TimelineScene");
    const { container } = render(
      <TimelineScene events={[{ label: "Event", date: "2024" }]} duration={60} />,
    );
    const html = container.innerHTML;
    expect(html).not.toContain("#0f0f23");
    expect(html).not.toContain("#7c5cbf");
  });

  it("CaptionOverlay: uses token colors", async () => {
    const { CaptionOverlay } = await import("../src/captions/CaptionOverlay");
    const { container } = render(<CaptionOverlay words={[]} />);
    expect(container.innerHTML).not.toContain("#ffeb3b");
  });

  it("LowerThird: uses token colors (no hardcoded literal hex)", async () => {
    const { LowerThird } = await import("../src/scenes/LowerThird");
    const { container } = render(<LowerThird title="Test" duration={60} />);
    const html = container.innerHTML;
    expect(html).not.toContain("#1a1a2e");
    expect(html).not.toContain("#ffeb3b");
  });

  it("OverlayCTA: uses token colors (no hardcoded literal hex)", async () => {
    const { OverlayCTA } = await import("../src/scenes/OverlayCTA");
    const { container } = render(<OverlayCTA title="Test" duration={60} />);
    const html = container.innerHTML;
    expect(html).not.toContain("#1a1a2e");
    expect(html).not.toContain("#ffeb3b");
  });

  it("AnimatedMindMap: no hardcoded colors", async () => {
    const { AnimatedMindMap } = await import("../src/components/AnimatedMindMap");
    const { container } = render(
      <AnimatedMindMap
        root={{ id: "root", label: "Root", children: [] }}
        wordTimestamps={[]}
        sceneStartFrame={0}
      />,
    );
    const html = container.innerHTML;
    expect(html).not.toContain("#0f0f23");
    expect(html).not.toContain("#1a1a3e");
  });
});
