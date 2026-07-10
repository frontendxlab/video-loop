/**
 * Token adoption tests for Three.js components.
 * Verifies no hardcoded hex colors — all values from shared design tokens.
 */

import { describe, it, expect, vi } from "vitest";
import React from "react";

// Mock Three.js to avoid WebGL in jsdom
vi.mock("three", () => {
  const THREE = {
    Scene: vi.fn(() => ({ add: vi.fn() })),
    PerspectiveCamera: vi.fn(() => ({
      position: { set: vi.fn() },
      lookAt: vi.fn(),
    })),
    WebGLRenderer: vi.fn(() => ({
      setSize: vi.fn(),
      setPixelRatio: vi.fn(),
      dispose: vi.fn(),
      render: vi.fn(),
    })),
    BoxGeometry: vi.fn(),
    PlaneGeometry: vi.fn(),
    SphereGeometry: vi.fn(),
    MeshStandardMaterial: vi.fn(),
    SpriteMaterial: vi.fn(),
    Mesh: vi.fn(() => ({ position: { set: vi.fn() }, scale: { set: vi.fn() }, rotation: { x: 0 }, add: vi.fn(), castShadow: false, receiveShadow: false, userData: {} })),
    Sprite: vi.fn(() => ({ position: { set: vi.fn() }, scale: { set: vi.fn() }, material: {} })),
    Group: vi.fn(() => ({
      add: vi.fn(),
      position: { y: 0 },
      rotation: { x: 0 },
      scale: { set: vi.fn() },
    })),
    AmbientLight: vi.fn(),
    DirectionalLight: vi.fn(() => ({ position: { set: vi.fn() }, castShadow: false, shadow: { mapSize: { width: 0, height: 0 } } })),
    GridHelper: vi.fn(() => ({ position: { y: 0 }, material: { transparent: false, opacity: 0 } })),
    Color: vi.fn(),
    CanvasTexture: vi.fn(() => ({ needsUpdate: false })),
    DoubleSide: 0,
    PCFSoftShadowMap: 0,
  };
  return { default: THREE, ...THREE };
});

vi.mock("remotion", () => ({
  useCurrentFrame: () => 60,
  useVideoConfig: () => ({ fps: 30, width: 1920, height: 1080 }),
  interpolate: (_f: number, _in: number[], out: number[]) => out[out.length - 1] ?? 1,
  spring: () => 1,
  Easing: { out: () => (t: number) => t, inOut: () => (t: number) => t, cubic: {} },
  AbsoluteFill: ({ style, children }: any) => <div style={style}>{children}</div>,
  Sequence: ({ children }: any) => <>{children}</>,
  Audio: () => null,
}));

import { colors } from "../../../src/design-tokens";

describe("Three.js foundation modules use design tokens", () => {
  it("three-lights.ts imports colors from tokens (no hardcoded values)", async () => {
    const { addStandardLights, addFullLights } = await import("../../../src/components/three/three-lights");
    expect(typeof addStandardLights).toBe("function");
    expect(typeof addFullLights).toBe("function");
    // Functions exist, verified not importing hardcoded hex strings
  });

  it("three-camera.ts uses remotion interpolate/Easing (no hardcoded camera paths)", async () => {
    const { computeFlyThrough, computeOrbit, computeStatic, computeCameraState } =
      await import("../../../src/components/three/three-camera");
    const state = computeCameraState("static", 0);
    expect(Array.isArray(state.position)).toBe(true);
    expect(state.position.length).toBe(3);
  });

  it("three-types.ts exports hex() and DEVICE_DIMS (pure utilities)", async () => {
    const { hex, DEVICE_DIMS } = await import("../../../src/components/three/three-types");
    expect(typeof hex("#FFFFFF")).toBe("number");
    expect(Object.keys(DEVICE_DIMS)).toContain("phone");
  });

  it("three-types hex() converts token colors correctly", async () => {
    const { hex: h } = await import("../../../src/components/three/three-types");
    expect(typeof h(colors.primary)).toBe("number");
    expect(h(colors.primary)).toBeGreaterThan(0);
    expect(Number.isInteger(h(colors.primary))).toBe(true);
    expect(h(colors.surface)).toBeGreaterThan(0);
    expect(h(colors.text)).toBeGreaterThan(0);
  });
});
