/** RankingBarScene tests — pure animation helpers + schema + token adoption. */

import { describe, it, expect } from "vitest";
import {
  RankingBarSceneSchema,
  RankingBarItemSchema,
  calcStaggerDelay,
  calcBarGrowProgress,
  calcBarHeight,
  calcCameraX,
  calcOrbitAngle,
  calcTitleOpacity,
} from "../../src/scenes/RankingBarScene";

describe("RankingBarScene", () => {
  /* ── Schema ── */

  describe("schema", () => {
    it("rejects empty items", () => {
      const r = RankingBarSceneSchema.safeParse({ type: "ranking-bar", items: [], duration: 60 });
      expect(r.success).toBe(false);
    });

    it("rejects single item (min 2)", () => {
      const r = RankingBarSceneSchema.safeParse({
        type: "ranking-bar",
        items: [{ rank: 1, label: "A", value: 100 }],
        duration: 60,
      });
      expect(r.success).toBe(false);
    });

    it("rejects missing duration", () => {
      const r = RankingBarSceneSchema.safeParse({
        type: "ranking-bar",
        items: [{ rank: 1, label: "A", value: 100 }, { rank: 2, label: "B", value: 50 }],
      });
      expect(r.success).toBe(false);
    });

    it("accepts valid minimal props", () => {
      const r = RankingBarSceneSchema.safeParse({
        type: "ranking-bar",
        items: [
          { rank: 1, label: "Game A", value: 100 },
          { rank: 2, label: "Game B", value: 50 },
        ],
        duration: 60,
      });
      expect(r.success).toBe(true);
    });

    it("accepts up to 20 items", () => {
      const items = Array.from({ length: 20 }, (_, i) => ({
        rank: i + 1,
        label: `Game ${i + 1}`,
        value: 100 - i * 4,
      }));
      const r = RankingBarSceneSchema.safeParse({ type: "ranking-bar", items, duration: 120 });
      expect(r.success).toBe(true);
    });

    it("rejects more than 20 items", () => {
      const items = Array.from({ length: 21 }, (_, i) => ({
        rank: i + 1,
        label: `Game ${i + 1}`,
        value: 100 - i * 4,
      }));
      const r = RankingBarSceneSchema.safeParse({ type: "ranking-bar", items, duration: 120 });
      expect(r.success).toBe(false);
    });

    it("defaults cameraPath to fly-through", () => {
      const r = RankingBarSceneSchema.parse({
        type: "ranking-bar",
        items: [{ rank: 1, label: "A", value: 10 }, { rank: 2, label: "B", value: 5 }],
        duration: 60,
      });
      expect(r.cameraPath).toBe("fly-through");
    });

    it("defaults showValues to true", () => {
      const r = RankingBarSceneSchema.parse({
        type: "ranking-bar",
        items: [{ rank: 1, label: "A", value: 10 }, { rank: 2, label: "B", value: 5 }],
        duration: 60,
      });
      expect(r.showValues).toBe(true);
    });

    it("defaults sceneStartFrame to 0", () => {
      const r = RankingBarSceneSchema.parse({
        type: "ranking-bar",
        items: [{ rank: 1, label: "A", value: 10 }, { rank: 2, label: "B", value: 5 }],
        duration: 60,
      });
      expect(r.sceneStartFrame).toBe(0);
    });

    it("accepts optional color per item", () => {
      const r = RankingBarSceneSchema.parse({
        type: "ranking-bar",
        items: [
          { rank: 1, label: "A", value: 10, color: "#FF0000" },
          { rank: 2, label: "B", value: 5 },
        ],
        duration: 60,
      });
      expect(r.items[0].color).toBe("#FF0000");
      expect(r.items[1].color).toBeUndefined();
    });

    it("rejects cameraPath enum violations", () => {
      const r = RankingBarSceneSchema.safeParse({
        type: "ranking-bar",
        items: [{ rank: 1, label: "A", value: 10 }, { rank: 2, label: "B", value: 5 }],
        duration: 60,
        cameraPath: "zoom",
      });
      expect(r.success).toBe(false);
    });
  });

  /* ── RankingBarItemSchema ── */

  describe("RankingBarItemSchema", () => {
    it("rejects non-positive rank", () => {
      const r = RankingBarItemSchema.safeParse({ rank: 0, label: "A", value: 100 });
      expect(r.success).toBe(false);
    });

    it("rejects negative value", () => {
      const r = RankingBarItemSchema.safeParse({ rank: 1, label: "A", value: -1 });
      expect(r.success).toBe(false);
    });

    it("rejects empty label", () => {
      const r = RankingBarItemSchema.safeParse({ rank: 1, label: "", value: 100 });
      expect(r.success).toBe(false);
    });

    it("accepts valid item", () => {
      const r = RankingBarItemSchema.safeParse({ rank: 1, label: "Game A", value: 100_000_000 });
      expect(r.success).toBe(true);
    });

    it("accepts optional color", () => {
      const r = RankingBarItemSchema.parse({ rank: 1, label: "A", value: 100, color: "#22C55E" });
      expect(r.color).toBe("#22C55E");
    });
  });

  /* ── calcStaggerDelay ── */

  describe("calcStaggerDelay", () => {
    it("first bar has 0 delay", () => {
      expect(calcStaggerDelay(0, 5)).toBe(0);
    });

    it("later bars have increasing delay", () => {
      expect(calcStaggerDelay(1, 5)).toBe(4);
      expect(calcStaggerDelay(4, 5)).toBe(16);
    });

    it("total bars argument does not affect per-index delay", () => {
      expect(calcStaggerDelay(2, 5)).toBe(8);
      expect(calcStaggerDelay(2, 20)).toBe(8);
    });
  });

  /* ── calcBarGrowProgress ── */

  describe("calcBarGrowProgress", () => {
    it("is 0 before stagger delay", () => {
      expect(calcBarGrowProgress(0, 0, 30)).toBe(0);
      expect(calcBarGrowProgress(3, 8, 30)).toBe(0);
    });

    it("is > 0 after delay, early frame", () => {
      const p = calcBarGrowProgress(12, 8, 30);
      expect(p).toBeGreaterThan(0);
      expect(p).toBeLessThan(1);
    });

    it("approaches 1 by frame delay+90 (3s)", () => {
      expect(calcBarGrowProgress(0 + 90, 0, 30)).toBeCloseTo(1, 5);
      expect(calcBarGrowProgress(8 + 90, 8, 30)).toBeCloseTo(1, 5);
    });
  });

  /* ── calcBarHeight ── */

  describe("calcBarHeight", () => {
    it("returns MIN_BAR_HEIGHT at progress 0", () => {
      expect(calcBarHeight(100, 100, 0)).toBeCloseTo(0.15, 2);
    });

    it("returns MAX_BAR_HEIGHT for max value at progress 1", () => {
      expect(calcBarHeight(100, 100, 1)).toBeCloseTo(5.5, 1);
    });

    it("scales proportionally for half value", () => {
      const maxVal = 100;
      const fullHeight = calcBarHeight(maxVal, maxVal, 1);
      const halfHeight = calcBarHeight(maxVal * 0.5, maxVal, 1);
      // half value gets half max bar height (roughly)
      expect(halfHeight).toBeGreaterThan(fullHeight * 0.45);
      expect(halfHeight).toBeLessThan(fullHeight * 0.55);
    });

    it("clamps at max bar height for values above max", () => {
      expect(calcBarHeight(200, 100, 1)).toBeCloseTo(5.5, 1);
    });

    it("returns MIN_BAR_HEIGHT for value 0", () => {
      expect(calcBarHeight(0, 100, 1)).toBeCloseTo(0.15, 2);
    });

    it("interpolates between progress values", () => {
      const p0 = calcBarHeight(100, 100, 0);
      const p50 = calcBarHeight(100, 100, 0.5);
      const p100 = calcBarHeight(100, 100, 1);
      expect(p50).toBeGreaterThan(p0);
      expect(p100).toBeGreaterThan(p50);
    });
  });

  /* ── calcCameraX ── */

  describe("calcCameraX", () => {
    it("starts at -3.5 at progress 0", () => {
      expect(calcCameraX(0)).toBeCloseTo(-3.5, 2);
    });

    it("ends at 3.5 at progress 1", () => {
      expect(calcCameraX(1)).toBeCloseTo(3.5, 2);
    });

    it("at 0.5 progress near center", () => {
      const mid = calcCameraX(0.5);
      expect(mid).toBeGreaterThan(-0.5);
      expect(mid).toBeLessThan(0.5);
    });

    it("clamps at -3.5 for negative progress", () => {
      expect(calcCameraX(-0.5)).toBeCloseTo(-3.5, 2);
    });

    it("clamps at 3.5 for progress > 1", () => {
      expect(calcCameraX(1.5)).toBeCloseTo(3.5, 2);
    });
  });

  /* ── calcOrbitAngle ── */

  describe("calcOrbitAngle", () => {
    it("starts at 0", () => {
      expect(calcOrbitAngle(0)).toBeCloseTo(0, 5);
    });

    it("ends at 2*PI", () => {
      expect(calcOrbitAngle(1)).toBeCloseTo(Math.PI * 2, 1);
    });

    it("at midpoint is near PI", () => {
      expect(calcOrbitAngle(0.5)).toBeGreaterThan(2.5);
      expect(calcOrbitAngle(0.5)).toBeLessThan(3.8);
    });
  });

  /* ── calcTitleOpacity ── */

  describe("calcTitleOpacity", () => {
    it("is 0 at frame 0", () => {
      expect(calcTitleOpacity(0, 30)).toBe(0);
    });

    it("is > 0 by frame 30 (1s)", () => {
      expect(calcTitleOpacity(30, 30)).toBeGreaterThan(0);
    });

    it("reaches 1 by frame 60 (2s)", () => {
      expect(calcTitleOpacity(60, 30)).toBe(1);
    });

    it("clamps at 1 beyond duration", () => {
      expect(calcTitleOpacity(120, 30)).toBe(1);
    });
  });
});
