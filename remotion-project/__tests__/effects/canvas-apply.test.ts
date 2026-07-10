import { describe, it, expect } from "vitest";
import {
  applyGlitch,
  applyVintage,
  applyMagnifier,
  renderTextContent,
} from "../../src/effects/canvas-apply";
import {
  computeGlitchOffsets,
  computeVintageParams,
  computeMagnifierDisplacement,
  compositeEffects,
} from "../../src/effects/composite";

function makeTestImage(
  w: number,
  h: number,
  fill: (x: number, y: number) => [number, number, number, number],
): Uint8ClampedArray {
  const d = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const [r, g, b, a] = fill(x, y);
      const i = (y * w + x) * 4;
      d[i] = r;
      d[i + 1] = g;
      d[i + 2] = b;
      d[i + 3] = a;
    }
  }
  return d;
}

function pixelsEqual(a: Uint8ClampedArray, b: Uint8ClampedArray): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

describe("applyGlitch", () => {
  it("returns same pixels when offsets are zero", () => {
    const w = 4, h = 4;
    const src = makeTestImage(w, h, (x, y) => [x * 64, y * 64, 128, 255]);
    const offsets = new Array(h).fill(0);
    const out = applyGlitch(src, w, h, offsets);
    expect(pixelsEqual(src, out)).toBe(true);
  });

  it("shifts row pixels by offset", () => {
    const w = 4, h = 2;
    const src = new Uint8ClampedArray(w * h * 4);
    for (let x = 0; x < w; x++) {
      const i = x * 4;
      src[i] = x * 50;
      src[i + 1] = 0;
      src[i + 2] = 0;
      src[i + 3] = 255;
    }
    for (let x = 0; x < w; x++) {
      const i = (w + x) * 4;
      src[i] = x * 50;
      src[i + 1] = 0;
      src[i + 2] = 0;
      src[i + 3] = 255;
    }

    const offsets = [1, -1];
    const out = applyGlitch(src, w, h, offsets);

    expect(out[0]).toBe(0);
    expect(out[1]).toBe(0);
    expect(out[2]).toBe(0);
    expect(out[3 * 4]).toBe(100);
  });

  it("handles offset beyond edge (all black)", () => {
    const w = 4, h = 1;
    const src = makeTestImage(w, h, () => [255, 255, 255, 255]);
    const offsets = [9];
    const out = applyGlitch(src, w, h, offsets);
    for (let i = 0; i < w * 4; i++) {
      expect(out[i]).toBe(0);
    }
  });
});

describe("applyVintage", () => {
  it("changes pixel colour via sepia", () => {
    const w = 2, h = 2;
    const white = makeTestImage(w, h, () => [255, 255, 255, 255]);
    const params = computeVintageParams({ type: "vintage" as const, grainIntensity: 0, sepiaMix: 1, vignetteStrength: 0 });
    const out = applyVintage(white, w, h, params, 0);
    const [r, g, b] = [out[0], out[1], out[2]];
    expect(r).toBeGreaterThan(0);
    expect(g).toBeGreaterThan(0);
    expect(b).toBeGreaterThan(0);
  });

  it("darkens corners with vignette", () => {
    const w = 5, h = 5;
    const white = makeTestImage(w, h, () => [200, 200, 200, 255]);
    const params = computeVintageParams({ type: "vintage" as const, grainIntensity: 0, sepiaMix: 0, vignetteStrength: 1 });
    const out = applyVintage(white, w, h, params, 0);
    const centreIdx = (2 * w + 2) * 4;
    const cornerIdx = 0;
    expect(out[centreIdx]).toBeGreaterThan(out[cornerIdx]);
  });

  it("is deterministic — same frame same output", () => {
    const w = 4, h = 4;
    const src = makeTestImage(w, h, () => [128, 128, 128, 255]);
    const params = computeVintageParams({ type: "vintage" as const, grainIntensity: 0.5, sepiaMix: 0.5, vignetteStrength: 0.3 });
    const a = applyVintage(src, w, h, params, 7);
    const b = applyVintage(src, w, h, params, 7);
    expect(pixelsEqual(a, b)).toBe(true);
  });
});

describe("applyMagnifier", () => {
  it("returns original when displacement is zero", () => {
    const w = 4, h = 4;
    const src = makeTestImage(w, h, (x, y) => (x + y) % 2 === 0 ? [255, 0, 0, 255] : [0, 0, 0, 255]);
    const map = Array.from({ length: h }, () => Array.from({ length: w }, () => ({ dx: 0, dy: 0 })));
    const out = applyMagnifier(src, w, h, map);
    expect(pixelsEqual(src, out)).toBe(true);
  });

  it("displaces pixels under magnifier radius", () => {
    const w = 8, h = 8;
    const src = makeTestImage(w, h, (x, y) => {
      if (x >= 3 && x <= 4 && y >= 3 && y <= 4) return [0, 0, 255, 255];
      return [255, 0, 0, 255];
    });
    const config = { type: "magnifier" as const, radius: 20, zoom: 1.5, centerX: 0.5, centerY: 0.5 };
    const map = computeMagnifierDisplacement(w, h, config);
    const out = applyMagnifier(src, w, h, map);
    expect(pixelsEqual(src, out)).toBe(false);
  });
});

describe("renderTextContent", () => {
  it("returns pixel buffer of expected size", () => {
    const pixels = renderTextContent("Test", undefined, 80, 60, "#0F172A", "#FFFFFF", "#F59E0B", "sans-serif");
    expect(pixels.length).toBe(80 * 60 * 4);
  });

  it("works with subtitle", () => {
    const pixels = renderTextContent("Title", "Sub", 80, 60, "#0F172A", "#FFFFFF", "#F59E0B", "sans-serif");
    expect(pixels.length).toBe(80 * 60 * 4);
  });

  it("is deterministic for same inputs", () => {
    const a = renderTextContent("Hello", "World", 40, 30, "#000", "#FFF", "#F00", "sans-serif");
    const b = renderTextContent("Hello", "World", 40, 30, "#000", "#FFF", "#F00", "sans-serif");
    expect(pixelsEqual(a, b)).toBe(true);
  });
});

describe("integrated pipelines", () => {
  it("runs glitch+vintage pipeline at small scale", () => {
    const w = 16, h = 16, frame = 5;
    const layers = [
      { type: "glitch" as const, intensity: 0.5, scanlineCount: 4, offsetMax: 3 },
      { type: "vintage" as const, grainIntensity: 0.1, sepiaMix: 0.3, vignetteStrength: 0.2 },
    ];
    const result = compositeEffects(layers, w, h, frame);
    let pixels = makeTestImage(w, h, () => [128, 128, 128, 255]);
    for (const layer of layers) {
      switch (layer.type) {
        case "glitch": if (result.glitchOffsets) pixels = applyGlitch(pixels, w, h, result.glitchOffsets); break;
        case "vintage": if (result.vintageParams) pixels = applyVintage(pixels, w, h, result.vintageParams, frame); break;
      }
    }
    expect(pixels.length).toBe(w * h * 4);
    expect(pixels[0]).not.toBe(128);
  });

  it("runs magnifier+glitch pipeline", () => {
    const w = 16, h = 16, frame = 10;
    const layers = [
      { type: "magnifier" as const, radius: 6, zoom: 2, centerX: 0.5, centerY: 0.5 },
      { type: "glitch" as const, intensity: 0.4, scanlineCount: 4, offsetMax: 3 },
    ];
    const result = compositeEffects(layers, w, h, frame);
    let pixels = makeTestImage(w, h, (x, y) => { const v = (x + y) % 256; return [v, v, v, 255]; });
    for (const layer of layers) {
      switch (layer.type) {
        case "glitch": if (result.glitchOffsets) pixels = applyGlitch(pixels, w, h, result.glitchOffsets); break;
        case "magnifier": if (result.magnifierMap) pixels = applyMagnifier(pixels, w, h, result.magnifierMap); break;
      }
    }
    expect(pixels.length).toBe(w * h * 4);
    const orig = makeTestImage(w, h, (x, y) => { const v = (x + y) % 256; return [v, v, v, 255]; });
    expect(pixelsEqual(pixels, orig)).toBe(false);
  });
});
