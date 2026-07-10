/** Unit tests for deterministic camera rig math. */

import { describe, it, expect } from "vitest";
import {
  computeFlyThrough,
  computeOrbit,
  computeStatic,
  computeCameraState,
} from "../../../src/components/three/three-camera";

describe("computeFlyThrough", () => {
  it("starts at xStart at progress 0", () => {
    const state = computeFlyThrough(0, { xStart: -3, xEnd: 3, y: 2, z: 5 });
    expect(state.position[0]).toBeCloseTo(-3);
    expect(state.position[1]).toBe(2);
    expect(state.position[2]).toBe(5);
  });

  it("ends at xEnd at progress 1", () => {
    const state = computeFlyThrough(1, { xStart: -3, xEnd: 3 });
    expect(state.position[0]).toBeCloseTo(3);
  });

  it("uses defaults when no config provided", () => {
    const state = computeFlyThrough(0);
    expect(state.position[0]).toBeCloseTo(-3.5);
    expect(state.position[1]).toBe(3.2);
    expect(state.position[2]).toBe(7.5);
  });

  it("lookAt is always [0, 1.5, 0]", () => {
    const s1 = computeFlyThrough(0);
    const s2 = computeFlyThrough(0.5);
    const s3 = computeFlyThrough(1);
    expect(s1.lookAt).toEqual([0, 1.5, 0]);
    expect(s2.lookAt).toEqual([0, 1.5, 0]);
    expect(s3.lookAt).toEqual([0, 1.5, 0]);
  });

  it("is deterministic (same input = same output)", () => {
    const a = computeFlyThrough(0.33);
    const b = computeFlyThrough(0.33);
    expect(a.position).toEqual(b.position);
  });

  it("clamps progress beyond [0,1]", () => {
    const s1 = computeFlyThrough(-0.5);
    const s2 = computeFlyThrough(1.5);
    expect(s1.position[0]).toBeCloseTo(-3.5);
    expect(s2.position[0]).toBeCloseTo(3.5);
  });
});

describe("computeOrbit", () => {
  it("starts at angle 0 at progress 0", () => {
    const state = computeOrbit(0, { radius: 5, height: 2 });
    expect(state.position[0]).toBeCloseTo(0);
    expect(state.position[2]).toBeCloseTo(5);
    expect(state.position[1]).toBe(2);
  });

  it("completes full circle at progress 1", () => {
    const state = computeOrbit(1, { radius: 5 });
    expect(state.position[0]).toBeCloseTo(0);
    expect(state.position[2]).toBeCloseTo(5);
  });

  it("is at opposite side at progress 0.5", () => {
    const state = computeOrbit(0.5, { radius: 5 });
    expect(state.position[0]).toBeCloseTo(0);
    expect(state.position[2]).toBeCloseTo(-5);
  });

  it("lookAt is always [0, targetY, 0]", () => {
    const state = computeOrbit(0.25, { targetY: 2 });
    expect(state.lookAt).toEqual([0, 2, 0]);
  });

  it("is deterministic", () => {
    const a = computeOrbit(0.7);
    const b = computeOrbit(0.7);
    expect(a.position).toEqual(b.position);
  });
});

describe("computeStatic", () => {
  it("returns default position when no config", () => {
    const state = computeStatic(0);
    expect(state.position).toEqual([0, 3.2, 7.5]);
    expect(state.lookAt).toEqual([0, 1.5, 0]);
  });

  it("returns custom position when configured", () => {
    const state = computeStatic(0, {
      position: [1, 2, 3],
      lookAt: [4, 5, 6],
    });
    expect(state.position).toEqual([1, 2, 3]);
    expect(state.lookAt).toEqual([4, 5, 6]);
  });

  it("is deterministic regardless of progress", () => {
    const a = computeStatic(0.5, { position: [1, 2, 3] });
    const b = computeStatic(0.9, { position: [1, 2, 3] });
    expect(a.position).toEqual(b.position);
  });
});

describe("computeCameraState", () => {
  it("dispatches fly-through for 'fly-through' rig", () => {
    const state = computeCameraState("fly-through", 0);
    expect(state.position[0]).toBeCloseTo(-3.5);
  });

  it("dispatches orbit for 'orbit' rig", () => {
    const state = computeCameraState("orbit", 0);
    expect(state.position[2]).toBeCloseTo(7.5);
  });

  it("dispatches static for 'static' rig", () => {
    const state = computeCameraState("static", 0);
    expect(state.position).toEqual([0, 3.2, 7.5]);
  });

  it("passes config through to rig function", () => {
    const state = computeCameraState("fly-through", 0, { xStart: -10, xEnd: 10 });
    expect(state.position[0]).toBeCloseTo(-10);
  });
});
