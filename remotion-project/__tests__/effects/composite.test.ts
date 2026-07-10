/** Tests for effect composite system. */

import { describe, it, expect } from "vitest";
import {
  computeGlitchOffsets,
  computeVintageParams,
  computeMagnifierDisplacement,
  compositeEffects,
} from "../../src/effects/composite";

describe("computeGlitchOffsets", () => {
  it("returns one offset per row", () => {
    const offsets = computeGlitchOffsets(10, { type: "glitch", intensity: 1, scanlineCount: 4, offsetMax: 8 }, 0);
    expect(offsets).toHaveLength(10);
  });

  it("offsets are within [-offsetMax, offsetMax]", () => {
    const offsets = computeGlitchOffsets(100, { type: "glitch", intensity: 1, scanlineCount: 8, offsetMax: 10 }, 0);
    for (const o of offsets) {
      expect(Math.abs(o)).toBeLessThanOrEqual(10);
    }
  });

  it("zero intensity produces all zero offsets", () => {
    const offsets = computeGlitchOffsets(50, { type: "glitch", intensity: 0, scanlineCount: 5, offsetMax: 8 }, 5);
    expect(offsets.every((o) => o === 0)).toBe(true);
  });

  it("changes with frame number", () => {
    const a = computeGlitchOffsets(20, { type: "glitch", intensity: 1, scanlineCount: 4, offsetMax: 8 }, 0);
    const b = computeGlitchOffsets(20, { type: "glitch", intensity: 1, scanlineCount: 4, offsetMax: 8 }, 10);
    expect(a).not.toEqual(b);
  });
});

describe("computeVintageParams", () => {
  it("returns sepia matrix, grain, vignette", () => {
    const p = computeVintageParams({ type: "vintage", grainIntensity: 0.2, sepiaMix: 0.5, vignetteStrength: 0.3 });
    expect(p.sepiaMatrix).toHaveLength(3);
    expect(p.sepiaMatrix[0]).toHaveLength(3);
    expect(p.grainNoise).toBe(0.2);
    expect(p.vignetteAlpha).toBe(0.7);
  });

  it("sepiaMix=0 yields identity-like matrix", () => {
    const p = computeVintageParams({ type: "vintage", grainIntensity: 0, sepiaMix: 0, vignetteStrength: 0 });
    // R row: 0.393*1 + 0.607*1 = 1.0, 0.769 - 0.769 = 0, 0.189 - 0.189 = 0
    expect(p.sepiaMatrix[0][0]).toBeCloseTo(1.0);
    expect(p.sepiaMatrix[0][1]).toBe(0);
    expect(p.sepiaMatrix[0][2]).toBe(0);
    // G row
    expect(p.sepiaMatrix[1][0]).toBe(0);
    expect(p.sepiaMatrix[1][1]).toBeCloseTo(1.0);
    expect(p.sepiaMatrix[1][2]).toBe(0);
  });

  it("sepiaMix=1 yields full sepia", () => {
    const p = computeVintageParams({ type: "vintage", grainIntensity: 0, sepiaMix: 1, vignetteStrength: 0 });
    // full sepia: R row = [0.393, 0.769, 0.189]
    expect(p.sepiaMatrix[0][0]).toBeCloseTo(0.393);
    expect(p.sepiaMatrix[0][1]).toBeCloseTo(0.769);
    expect(p.sepiaMatrix[0][2]).toBeCloseTo(0.189);
  });

  it("vignetteStrength=1 gives alpha 0", () => {
    const p = computeVintageParams({ type: "vintage", grainIntensity: 0, sepiaMix: 0, vignetteStrength: 1 });
    expect(p.vignetteAlpha).toBe(0);
  });
});

describe("computeMagnifierDisplacement", () => {
  const cfg = { type: "magnifier" as const, radius: 20, zoom: 2, centerX: 0.5, centerY: 0.5 };

  it("returns grid of correct dimensions", () => {
    const map = computeMagnifierDisplacement(40, 30, cfg);
    expect(map).toHaveLength(30);
    expect(map[0]).toHaveLength(40);
  });

  it("center pixel has zero displacement", () => {
    const map = computeMagnifierDisplacement(40, 40, cfg);
    // centre at (20,20)
    expect(map[20][20].dx).toBe(0);
    expect(map[20][20].dy).toBe(0);
  });

  it("pixels outside radius have zero displacement", () => {
    const map = computeMagnifierDisplacement(100, 100, cfg);
    // corner far outside
    expect(map[0][0]).toEqual({ dx: 0, dy: 0 });
    expect(map[99][99]).toEqual({ dx: 0, dy: 0 });
  });

  it("zoom=1 produces all-zero displacement", () => {
    const map = computeMagnifierDisplacement(40, 40, { ...cfg, zoom: 1 });
    const allZero = map.every((row) => row.every((p) => p.dx === 0 && p.dy === 0));
    expect(allZero).toBe(true);
  });
});

describe("compositeEffects", () => {
  it("empty layers returns empty result", () => {
    const r = compositeEffects([], 100, 100, 0);
    expect(r).toEqual({});
  });

  it("single glitch layer produces offsets", () => {
    const r = compositeEffects(
      [{ type: "glitch", intensity: 0.5, scanlineCount: 6, offsetMax: 4 }],
      100,
      50,
      3,
    );
    expect(r.glitchOffsets).toHaveLength(50);
    expect(r.vintageParams).toBeUndefined();
    expect(r.magnifierMap).toBeUndefined();
  });

  it("multiple layers produce all outputs", () => {
    const r = compositeEffects(
      [
        { type: "glitch", intensity: 0.5, scanlineCount: 6, offsetMax: 4 },
        { type: "vintage", grainIntensity: 0.1, sepiaMix: 0.4, vignetteStrength: 0.2 },
      ],
      100,
      50,
      0,
    );
    expect(r.glitchOffsets).toBeDefined();
    expect(r.vintageParams).toBeDefined();
    expect(r.magnifierMap).toBeUndefined();
  });

  it("all three effect types together", () => {
    const r = compositeEffects(
      [
        { type: "glitch", intensity: 0.3, scanlineCount: 4, offsetMax: 3 },
        { type: "vintage", grainIntensity: 0.05, sepiaMix: 0.3, vignetteStrength: 0.1 },
        { type: "magnifier", radius: 10, zoom: 1.5, centerX: 0.5, centerY: 0.5 },
      ],
      30,
      20,
      2,
    );
    expect(r.glitchOffsets).toBeDefined();
    expect(r.vintageParams).toBeDefined();
    expect(r.magnifierMap).toBeDefined();
  });
});
