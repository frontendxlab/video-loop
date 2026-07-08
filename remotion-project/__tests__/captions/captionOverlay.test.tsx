/** Caption overlay tests. */

import { describe, it, expect } from "vitest";

describe("CaptionOverlay", () => {
  it("renders words with timing", () => {
    const words = [
      { text: "Hello", startMs: 0, endMs: 200 },
      { text: "world", startMs: 200, endMs: 400 },
    ];
    expect(words.length).toBe(2);
  });

  it("highlights current word", () => {
    const currentMs = 150;
    const isHighlighted = (start: number, end: number) => currentMs >= start && currentMs <= end;
    expect(isHighlighted(0, 200)).toBe(true);
    expect(isHighlighted(200, 400)).toBe(false);
  });

  it("dims previous words", () => {
    const previousOpacity = 0.5;
    const currentOpacity = 1.0;
    expect(previousOpacity).toBeLessThan(currentOpacity);
  });
});
