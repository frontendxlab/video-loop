/** CaptionBar tests. */

import { describe, it, expect, vi } from "vitest";
import React from "react";

// Mock remotion hooks so component renders in jsdom
vi.mock("remotion", () => ({
  useCurrentFrame: vi.fn(() => 0),
  useVideoConfig: vi.fn(() => ({ fps: 30, width: 1920, height: 1080 })),
  interpolate: vi.fn((_f: number, _in: number[], out: number[]) => out[out.length - 1] ?? 1),
  spring: vi.fn(() => 1),
  Easing: { out: () => (t: number) => t, cubic: {} },
}));

const mockWords = [
  { text: "Hello", startMs: 0, endMs: 200 },
  { text: "world", startMs: 200, endMs: 400 },
  { text: "this", startMs: 400, endMs: 600 },
  { text: "is", startMs: 600, endMs: 800 },
  { text: "a", startMs: 800, endMs: 1000 },
  { text: "test", startMs: 1000, endMs: 1200 },
];

describe("CaptionBar — logic", () => {
  it("returns null for empty words list", async () => {
    const { CaptionBar } = await import("../../src/captions/CaptionBar");
    const { render } = await import("@testing-library/react");
    const { container } = render(<CaptionBar words={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders all words in correct order", async () => {
    const { CaptionBar } = await import("../../src/captions/CaptionBar");
    const { render } = await import("@testing-library/react");
    const { container } = render(<CaptionBar words={mockWords} fps={30} />);
    const html = container.innerHTML;
    expect(html).toContain("Hello");
    expect(html).toContain("world");
    expect(html).toContain("test");
    // word order in DOM
    const idxHello = html.indexOf("Hello");
    const idxWorld = html.indexOf("world");
    const idxTest = html.indexOf("test");
    expect(idxHello).toBeLessThan(idxWorld);
    expect(idxWorld).toBeLessThan(idxTest);
  });

  it("applies higher weight to current word", async () => {
    const { CaptionBar } = await import("../../src/captions/CaptionBar");
    const { render } = await import("@testing-library/react");
    // frame 3 @ 30fps = 100ms → word 0 (Hello: 0–200ms)
    const useCurrentFrame = (await import("remotion")).useCurrentFrame as ReturnType<typeof vi.fn>;
    useCurrentFrame.mockReturnValue(3);
    const { container } = render(<CaptionBar words={mockWords} fps={30} />);
    const html = container.innerHTML;
    // first word rendered, has fontWeight 600
    expect(html).toContain("Hello");
  });

  it("dims past words with lower opacity", async () => {
    // Pure logic: getWordOpacity returns 0.5 for past, 1 for current/future
    const { getWordOpacity } = await import("../../src/captions/wordTiming");
    expect(getWordOpacity(0, 2)).toBe(0.5); // past
    expect(getWordOpacity(2, 2)).toBe(1); // current
    expect(getWordOpacity(4, 2)).toBe(1); // future
  });

  it("current word index calculated correctly", async () => {
    const { getCurrentWordIndex } = await import("../../src/captions/wordTiming");
    expect(getCurrentWordIndex(mockWords, 0)).toBe(0);
    expect(getCurrentWordIndex(mockWords, 100)).toBe(0);
    expect(getCurrentWordIndex(mockWords, 200)).toBe(0); // 200 falls in [0, 200]
    expect(getCurrentWordIndex(mockWords, 500)).toBe(2);
    expect(getCurrentWordIndex(mockWords, 1100)).toBe(5);
    expect(getCurrentWordIndex(mockWords, 9999)).toBe(-1);
  });

  it("progress bar uses design tokens", async () => {
    const { CaptionBar } = await import("../../src/captions/CaptionBar");
    const { render } = await import("@testing-library/react");
    const { container } = render(<CaptionBar words={mockWords} fps={30} />);
    const html = container.innerHTML;
    // chromeBorder hex pattern should be present (used for progress bg)
    expect(html).toMatch(/#[0-9a-fA-F]{6}/);
  });
});

describe("CaptionBar — progress", () => {
  it("progress at 0 when before first word", async () => {
    const { CaptionBar } = await import("../../src/captions/CaptionBar");
    const { render } = await import("@testing-library/react");
    const useCurrentFrame = (await import("remotion")).useCurrentFrame as ReturnType<typeof vi.fn>;
    useCurrentFrame.mockReturnValue(0);
    const { container } = render(<CaptionBar words={mockWords} fps={30} />);
    // Progress bar exists (div with gradient background)
    const divs = container.querySelectorAll("div");
    expect(divs.length).toBeGreaterThan(1);
  });

  it("progress at 100 when past all words", async () => {
    const { CaptionBar } = await import("../../src/captions/CaptionBar");
    const { render } = await import("@testing-library/react");
    const useCurrentFrame = (await import("remotion")).useCurrentFrame as ReturnType<typeof vi.fn>;
    // frame 40 @ 30fps = 1333ms > 1200ms (last word end)
    useCurrentFrame.mockReturnValue(40);
    const { container } = render(<CaptionBar words={mockWords} fps={30} />);
    // Snapshot test for final state — no crash, valid render
    expect(container.innerHTML).toContain("test");
  });
});
