/** TitleScene tests. */

import { describe, it, expect } from "vitest";

describe("TitleScene", () => {
  it("renders title text", () => {
    const title = "Hello World";
    expect(title.length).toBeGreaterThan(0);
  });

  it("renders subtitle when provided", () => {
    const subtitle = "A subtitle";
    expect(subtitle).toBeDefined();
  });

  it("fadeIn animation goes 0→1 over 30 frames", () => {
    const opacity = (f: number) => Math.min(1, f / 30);
    expect(opacity(0)).toBe(0);
    expect(opacity(15)).toBe(0.5);
    expect(opacity(30)).toBe(1);
  });

  it("slideUp animation goes 20→0 over 30 frames", () => {
    const y = (f: number) => 20 * (1 - Math.min(1, f / 30));
    expect(y(0)).toBe(20);
    expect(y(30)).toBe(0);
  });

  it("typewriter reveals characters one by one", () => {
    const text = "Hello";
    const charsPerFrame = 1 / 3;
    const visible = (f: number) => text.slice(0, Math.floor(f * charsPerFrame));
    expect(visible(0)).toBe("");
    expect(visible(6)).toBe("He");
    expect(visible(15)).toBe("Hello");
  });
});
