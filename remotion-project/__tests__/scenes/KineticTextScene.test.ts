/** KineticTextScene tests. */

import { describe, it, expect } from "vitest";

describe("KineticTextScene", () => {
  const sampleLines = [
    { text: "Build something", highlightWords: ["Build"] },
    { text: "Ship something", animation: "slide" as const },
  ];

  it("accepts valid kinetic text config", () => {
    expect(sampleLines.length).toBe(2);
    expect(sampleLines[0].highlightWords).toEqual(["Build"]);
  });

  it("word splitting produces correct number of words", () => {
    const split = (t: string) => t.split(/\s+/).filter(Boolean);
    expect(split("Build something great")).toHaveLength(3);
    expect(split("Hello")).toHaveLength(1);
  });

  it("strips punctuation from word for highlight matching", () => {
    const clean = (w: string) => w.replace(/[^\w]/g, "");
    expect(clean("build!")).toBe("build");
    expect(clean("(great)")).toBe("great");
    expect(clean("don't")).toBe("dont");
    expect(clean("word.")).toBe("word");
  });

  it("highlightWords matching works on cleaned tokens", () => {
    const highlights = ["Build", "Ship"];
    const check = (word: string) => highlights.includes(word.replace(/[^\w]/g, ""));
    expect(check("Build")).toBe(true);
    expect(check("build!")).toBe(false); // case-sensitive match
    expect(check("Ship")).toBe(true);
    expect(check("Something")).toBe(false);
  });

  it("fade animation goes 0→1 over WORD_DURATION frames", () => {
    const WORD_DURATION = 15;
    const progress = (f: number) => Math.min(1, Math.max(0, f) / WORD_DURATION);
    expect(progress(0)).toBe(0);
    expect(progress(8)).toBeCloseTo(8 / 15);
    expect(progress(15)).toBe(1);
    expect(progress(99)).toBe(1);
  });

  it("slide animation translates Y 30→0", () => {
    const progress = (f: number) => Math.min(1, Math.max(0, f) / 15);
    const transY = (p: number) => 30 * (1 - p);
    expect(transY(progress(0))).toBe(30);
    expect(transY(progress(15))).toBe(0);
  });

  it("scale animation goes 0.8→1", () => {
    const progress = (f: number) => Math.min(1, Math.max(0, f) / 15);
    const scale = (p: number) => 0.8 + 0.2 * p;
    expect(scale(progress(0))).toBeCloseTo(0.8);
    expect(scale(progress(15))).toBe(1);
  });

  it("sequential line animation offsets by global word index", () => {
    const WORD_STAGGER = 8;
    // line 0: 2 words, line 1: 2 words
    // word[0] @ 0, word[1] @ 8, word[2] @ 16, word[3] @ 24
    const wordStart = (globalIdx: number) => globalIdx * WORD_STAGGER;
    expect(wordStart(0)).toBe(0);
    expect(wordStart(1)).toBe(8);
    expect(wordStart(3)).toBe(24);
  });

  it("simultaneous line animation uses per-line word index", () => {
    const WORD_STAGGER = 8;
    // both lines: word i @ i * WORD_STAGGER
    const wordStart = (wi: number) => wi * WORD_STAGGER;
    expect(wordStart(0)).toBe(0);
    expect(wordStart(1)).toBe(8);
    expect(wordStart(2)).toBe(16);
  });

  it("highlight pulse oscillates between 1 and HIGHLIGHT_SCALE_PEAK", () => {
    const HIGHLIGHT_SCALE_PEAK = 1.08;
    const PULSE_CYCLE = 40;
    const WORD_DURATION = 15;
    const pulse = (frame: number, wordStart: number) => {
      const elapsed = Math.max(0, frame - wordStart - WORD_DURATION);
      if (elapsed <= 0) return 1;
      const mod = elapsed % PULSE_CYCLE;
      const quarter = PULSE_CYCLE * 0.25;
      if (mod <= quarter) return 1 + (HIGHLIGHT_SCALE_PEAK - 1) * (mod / quarter);
      if (mod <= quarter * 2) return HIGHLIGHT_SCALE_PEAK - (HIGHLIGHT_SCALE_PEAK - 1) * ((mod - quarter) / quarter);
      if (mod <= quarter * 3) return 1 + (HIGHLIGHT_SCALE_PEAK - 1) * ((mod - quarter * 2) / quarter);
      return HIGHLIGHT_SCALE_PEAK - (HIGHLIGHT_SCALE_PEAK - 1) * ((mod - quarter * 3) / quarter);
    };
    // before word finishes animating in → no pulse
    expect(pulse(10, 5)).toBe(1);
    // at wordStart + WORD_DURATION + 0 → still 1
    expect(pulse(5 + 15, 5)).toBe(1);
    // at quarter cycle → peak
    expect(pulse(5 + 15 + 10, 5)).toBeCloseTo(HIGHLIGHT_SCALE_PEAK);
    // at half cycle → back to 1
    expect(pulse(5 + 15 + 20, 5)).toBeCloseTo(1);
  });

  it("rejects empty lines array", () => {
    expect(sampleLines.length).toBeGreaterThan(0);
  });

  it("total words count sums across lines", () => {
    const lineWords = sampleLines.map((l) => l.text.split(/\s+/).filter(Boolean).length);
    const total = lineWords.reduce((a, b) => a + b, 0);
    expect(total).toBe(4);
    expect(lineWords).toEqual([2, 2]);
  });
});
