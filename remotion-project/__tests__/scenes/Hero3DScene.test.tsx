/** Hero3DScene tests — pure animation helpers + schema + token adoption. */

import { describe, it, expect } from "vitest";
import { Hero3DSceneSchema, calcRiseProgress, calcTilt, calcScale, calcOverlayOpacity } from "../../src/scenes/Hero3DScene";

describe("Hero3DScene", () => {
  /* ── Schema ── */

  describe("schema", () => {
    it("rejects missing title", () => {
      const r = Hero3DSceneSchema.safeParse({ duration: 60 });
      expect(r.success).toBe(false);
    });

    it("rejects missing duration", () => {
      const r = Hero3DSceneSchema.safeParse({ type: "hero3d", title: "Hi" });
      expect(r.success).toBe(false);
    });

    it("accepts valid minimal props", () => {
      const r = Hero3DSceneSchema.safeParse({ type: "hero3d", title: "Hello", duration: 60 });
      expect(r.success).toBe(true);
    });

    it("defaults deviceType to phone", () => {
      const r = Hero3DSceneSchema.parse({ type: "hero3d", title: "X", duration: 30 });
      expect(r.deviceType).toBe("phone");
    });

    it("accepts laptop deviceType", () => {
      const r = Hero3DSceneSchema.parse({ type: "hero3d", title: "X", duration: 30, deviceType: "laptop" });
      expect(r.deviceType).toBe("laptop");
    });

    it("accepts monitor deviceType", () => {
      const r = Hero3DSceneSchema.parse({ type: "hero3d", title: "X", duration: 30, deviceType: "monitor" });
      expect(r.deviceType).toBe("monitor");
    });

    it("accepts optional subtitle", () => {
      const r = Hero3DSceneSchema.parse({ type: "hero3d", title: "X", subtitle: "Sub", duration: 30 });
      expect(r.subtitle).toBe("Sub");
    });

    it("defaults sceneStartFrame to 0", () => {
      const r = Hero3DSceneSchema.parse({ type: "hero3d", title: "X", duration: 30 });
      expect(r.sceneStartFrame).toBe(0);
    });

    it("rejects invalid deviceType", () => {
      const r = Hero3DSceneSchema.safeParse({ type: "hero3d", title: "X", duration: 30, deviceType: "tablet" });
      expect(r.success).toBe(false);
    });
  });

  /* ── calcRiseProgress ── */

  describe("calcRiseProgress", () => {
    it("starts at 0 on frame 0", () => {
      expect(calcRiseProgress(0, 30)).toBe(0);
    });

    it("reaches ~1 by frame 90 (3s)", () => {
      expect(calcRiseProgress(90, 30)).toBeCloseTo(1, 5);
    });

    it("is > 0 by frame 10", () => {
      expect(calcRiseProgress(10, 30)).toBeGreaterThan(0);
    });
  });

  /* ── calcTilt ── */

  describe("calcTilt", () => {
    it("starts at 0.5 rad at progress 0", () => {
      expect(calcTilt(0)).toBeCloseTo(0.5, 2);
    });

    it("ends near 0.05 rad at progress 1", () => {
      expect(calcTilt(1)).toBeCloseTo(0.05, 2);
    });

    it("decreases overall from start to end", () => {
      expect(calcTilt(1)).toBeLessThan(calcTilt(0));
    });
  });

  /* ── calcScale ── */

  describe("calcScale", () => {
    it("starts at 0.7 at progress 0", () => {
      expect(calcScale(0)).toBeCloseTo(0.7, 2);
    });

    it("ends at 1 at progress 1", () => {
      expect(calcScale(1)).toBeCloseTo(1, 5);
    });

    it("increases monotonically", () => {
      for (let i = 1; i <= 20; i++) {
        const p = i / 20;
        const prev = (i - 1) / 20;
        expect(calcScale(p)).toBeGreaterThanOrEqual(calcScale(prev) - 0.001);
      }
    });
  });

  /* ── calcOverlayOpacity ── */

  describe("calcOverlayOpacity", () => {
    it("is 0 at progress 0", () => {
      expect(calcOverlayOpacity(0)).toBe(0);
    });

    it("is 0 still at progress 0.5 (text not visible until device rises)", () => {
      expect(calcOverlayOpacity(0.5)).toBe(0);
    });

    it("reaches 1 at progress 1", () => {
      expect(calcOverlayOpacity(1)).toBe(1);
    });

    it("is > 0 at progress 0.75", () => {
      expect(calcOverlayOpacity(0.75)).toBeGreaterThan(0);
    });

    it("stays at 1 for progress > 1 (clamped)", () => {
      expect(calcOverlayOpacity(1.5)).toBe(1);
    });
  });
});
