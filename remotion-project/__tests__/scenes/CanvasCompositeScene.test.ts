import { describe, it, expect } from "vitest";
import { CanvasCompositeSceneSchema } from "../../src/scenes/CanvasCompositeScene";

describe("CanvasCompositeSceneSchema", () => {
  it("validates glitch+vintage scene", () => {
    const input = {
      type: "canvas-composite" as const,
      title: "Retro Glitch",
      subtitle: "VHS vibes",
      layers: [
        { type: "glitch" as const, intensity: 0.6, scanlineCount: 16, offsetMax: 10 },
        { type: "vintage" as const, grainIntensity: 0.2, sepiaMix: 0.5, vignetteStrength: 0.3 },
      ],
      duration: 120,
    };
    const result = CanvasCompositeSceneSchema.safeParse(input);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.type).toBe("canvas-composite");
      expect(result.data.layers.length).toBe(2);
      expect(result.data.layers[0].type).toBe("glitch");
      expect(result.data.layers[1].type).toBe("vintage");
    }
  });

  it("validates magnifier+glitch scene", () => {
    const input = {
      type: "canvas-composite" as const,
      title: "Lens Distort",
      layers: [
        { type: "magnifier" as const, radius: 100, zoom: 2, centerX: 0.5, centerY: 0.5 },
        { type: "glitch" as const, intensity: 0.4, scanlineCount: 8, offsetMax: 6 },
      ],
      duration: 90,
    };
    const result = CanvasCompositeSceneSchema.safeParse(input);
    expect(result.success).toBe(true);
  });

  it("validates single glitch-only scene", () => {
    const input = {
      type: "canvas-composite" as const,
      title: "Glitch Only",
      layers: [{ type: "glitch" as const, intensity: 0.5, scanlineCount: 12, offsetMax: 8 }],
      duration: 60,
    };
    const result = CanvasCompositeSceneSchema.safeParse(input);
    expect(result.success).toBe(true);
  });

  it("rejects empty layers", () => {
    const input = { type: "canvas-composite" as const, title: "No effects", layers: [], duration: 60 };
    const result = CanvasCompositeSceneSchema.safeParse(input);
    expect(result.success).toBe(false);
  });

  it("rejects missing title", () => {
    const input = { type: "canvas-composite" as const, layers: [{ type: "glitch" as const, intensity: 0.5 }], duration: 60 };
    const result = CanvasCompositeSceneSchema.safeParse(input);
    expect(result.success).toBe(false);
  });

  it("defaults effect fields", () => {
    const input = { type: "canvas-composite" as const, title: "Defaults", layers: [{ type: "glitch" as const } as any, { type: "vintage" as const } as any], duration: 90 };
    const result = CanvasCompositeSceneSchema.safeParse(input);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.layers[0].intensity).toBe(0.5);
      expect(result.data.layers[0].scanlineCount).toBe(12);
      expect(result.data.layers[1].grainIntensity).toBe(0.15);
    }
  });

  it("validates success directly", () => {
    const input = { type: "canvas-composite" as const, title: "Direct test", layers: [{ type: "vintage" as const, grainIntensity: 0.2, sepiaMix: 0.5, vignetteStrength: 0.3 }], duration: 90 };
    const result = CanvasCompositeSceneSchema.safeParse(input);
    expect(result.success).toBe(true);
  });
});
