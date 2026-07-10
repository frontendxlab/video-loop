/** ThreeScene + ThreeSceneExample tests. */

import { describe, it, expect, vi } from "vitest";

// Mock @remotion/three to avoid @react-three/fiber WebGL requirement in jsdom
vi.mock("@remotion/three", () => ({
  ThreeCanvas: ({ children }: { children: React.ReactNode }) => children,
}));

import { ThreeSceneExampleSchema } from "../../src/scenes/ThreeSceneExample";

describe("ThreeSceneExampleSchema", () => {
  it("validates 'three' type scene", () => {
    const result = ThreeSceneExampleSchema.parse({ type: "three", duration: 150 });
    expect(result.type).toBe("three");
    expect(result.duration).toBe(150);
  });

  it("rejects negative duration", () => {
    expect(() => ThreeSceneExampleSchema.parse({ type: "three", duration: -1 })).toThrow();
  });

  it("rejects missing type", () => {
    expect(() => ThreeSceneExampleSchema.parse({ duration: 150 })).toThrow();
  });

  it("rejects wrong type literal", () => {
    expect(() => ThreeSceneExampleSchema.parse({ type: "title", duration: 150 })).toThrow();
  });

  it("rejects zero duration", () => {
    expect(() => ThreeSceneExampleSchema.parse({ type: "three", duration: 0 })).toThrow();
  });
});

describe("ThreeScene (base helper)", () => {
  it("exists and exports expected interface", async () => {
    const mod = await import("../../src/components/three/ThreeScene");
    expect(mod.ThreeScene).toBeDefined();
    expect(typeof mod.ThreeScene).toBe("function");
  });
});
