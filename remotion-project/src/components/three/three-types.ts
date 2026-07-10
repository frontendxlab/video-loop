/**
 * Shared Three.js types, color conversion, and device dimension constants.
 * Pure functions — no React/Three.js runtime deps, fully testable.
 */

/** Convert hex string (#RRGGBB) to integer for Three.js Color. */
export function hex(c: string): number {
  return parseInt(c.slice(1), 16);
}

/** Minimal handle returned by imperative Three.js scene setup. */
export interface ThreeSceneHandle {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
}

/** Device form-factor dimensions for 3D device scenes. */
export const DEVICE_DIMS = {
  phone:    { w: 1.2, h: 2.4, d: 0.1, inset: 0.06 },
  laptop:   { w: 3.0, h: 2.0, d: 0.12, inset: 0.07 },
  monitor:  { w: 3.5, h: 2.2, d: 0.14, inset: 0.08 },
} as const;

export type DeviceType = keyof typeof DEVICE_DIMS;

/** Supported camera motion rigs for 3D scenes. */
export type CameraRigType = "fly-through" | "orbit" | "static";

/** 3D camera state (position + look-at target). */
export interface CameraState {
  position: [number, number, number];
  lookAt: [number, number, number];
}
