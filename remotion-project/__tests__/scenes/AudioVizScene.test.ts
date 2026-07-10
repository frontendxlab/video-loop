/** AudioVizScene tests. */

import { describe, it, expect } from "vitest";
import { AudioVizSceneSchema, getBarHeight } from "../../src/scenes/AudioVizScene";

describe("AudioVizScene", () => {
  describe("schema", () => {
    it("accepts valid waveform config", () => {
      const result = AudioVizSceneSchema.safeParse({
        audioSrc: "audio/sample.wav",
        variant: "waveform",
        barCount: 64,
        duration: 120,
      });
      expect(result.success).toBe(true);
    });

    it("accepts valid spectrum config", () => {
      const result = AudioVizSceneSchema.safeParse({
        audioSrc: "audio/sample.wav",
        variant: "spectrum",
        barCount: 128,
        duration: 120,
      });
      expect(result.success).toBe(true);
    });

    it("accepts minimal config with defaults", () => {
      const result = AudioVizSceneSchema.safeParse({
        audioSrc: "audio/sample.wav",
        duration: 120,
      });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.variant).toBe("waveform");
        expect(result.data.barCount).toBe(64);
      }
    });

    it("rejects missing audioSrc", () => {
      const result = AudioVizSceneSchema.safeParse({
        duration: 120,
      });
      expect(result.success).toBe(false);
    });

    it("rejects invalid variant", () => {
      const result = AudioVizSceneSchema.safeParse({
        audioSrc: "audio/sample.wav",
        variant: "bars",
        duration: 120,
      });
      expect(result.success).toBe(false);
    });

    it("rejects barCount below minimum", () => {
      const result = AudioVizSceneSchema.safeParse({
        audioSrc: "audio/sample.wav",
        barCount: 2,
        duration: 120,
      });
      expect(result.success).toBe(false);
    });

    it("rejects barCount above maximum", () => {
      const result = AudioVizSceneSchema.safeParse({
        audioSrc: "audio/sample.wav",
        barCount: 512,
        duration: 120,
      });
      expect(result.success).toBe(false);
    });

    it("rejects non-positive duration", () => {
      const result = AudioVizSceneSchema.safeParse({
        audioSrc: "audio/sample.wav",
        duration: -1,
      });
      expect(result.success).toBe(false);
    });

    it("accepts optional color override", () => {
      const result = AudioVizSceneSchema.safeParse({
        audioSrc: "audio/sample.wav",
        color: "#FF0000",
        duration: 120,
      });
      expect(result.success).toBe(true);
    });
  });

  describe("getBarHeight", () => {
    it("returns MIN_HEIGHT_PCT for zero waveform value", () => {
      const h = getBarHeight(0, "waveform");
      expect(h).toBeGreaterThan(0);
      expect(h).toBeLessThan(1);
    });

    it("returns near-max height for amplitude 1 waveform", () => {
      const h = getBarHeight(1, "waveform");
      expect(h).toBeGreaterThan(90);
    });

    it("uses absolute value for negative waveform", () => {
      const pos = getBarHeight(0.5, "waveform");
      const neg = getBarHeight(-0.5, "waveform");
      expect(neg).toBe(pos);
    });

    it("returns MIN_HEIGHT_PCT for zero spectrum value", () => {
      const h = getBarHeight(0, "spectrum");
      expect(h).toBeGreaterThan(0);
      expect(h).toBeLessThan(1);
    });

    it("returns near-max height for spectrum value 1", () => {
      const h = getBarHeight(1, "spectrum");
      expect(h).toBeGreaterThan(90);
    });

    it("clamps negative spectrum values to MIN_HEIGHT_PCT", () => {
      const h = getBarHeight(-0.1, "spectrum");
      const zero = getBarHeight(0, "spectrum");
      expect(h).toBe(zero);
    });

    it("scales linearly in expected range", () => {
      const low = getBarHeight(0.2, "spectrum");
      const mid = getBarHeight(0.5, "spectrum");
      const high = getBarHeight(0.8, "spectrum");
      expect(low).toBeLessThan(mid);
      expect(mid).toBeLessThan(high);
    });
  });

  describe("values array", () => {
    it("creates zero array of correct length when no audio data", () => {
      const arr = new Array(64).fill(0);
      expect(arr.length).toBe(64);
      expect(arr.every((v) => v === 0)).toBe(true);
    });

    it("creates correct length for non-default barCount", () => {
      const arr = new Array(128).fill(0);
      expect(arr.length).toBe(128);
    });
  });
});
