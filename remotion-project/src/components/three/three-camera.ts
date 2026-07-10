/**
 * Deterministic camera rig math for Three.js Remotion scenes.
 *
 * Each function is a pure transformation of `progress [0,1]` into a
 * camera position, making it fully testable without Three.js or React.
 */

import { interpolate, Easing } from "remotion";
import type { CameraRigType, CameraState } from "./three-types";

/* ── Rig: fly-through (camera sweeps left-to-right) ── */

export interface FlyThroughConfig {
  xStart?: number;
  xEnd?: number;
  y?: number;
  z?: number;
}

export function computeFlyThrough(
  progress: number,
  config: FlyThroughConfig = {},
): CameraState {
  const { xStart = -3.5, xEnd = 3.5, y = 3.2, z = 7.5 } = config;
  const x = interpolate(progress, [0, 1], [xStart, xEnd], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });
  return { position: [x, y, z], lookAt: [0, 1.5, 0] };
}

/* ── Rig: orbit (camera circles around origin) ── */

export interface OrbitConfig {
  radius?: number;
  height?: number;
  targetY?: number;
}

export function computeOrbit(
  progress: number,
  config: OrbitConfig = {},
): CameraState {
  const { radius = 7.5, height = 3.2, targetY = 1.5 } = config;
  const angle = interpolate(progress, [0, 1], [0, Math.PI * 2], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });
  return {
    position: [Math.sin(angle) * radius, height, Math.cos(angle) * radius],
    lookAt: [0, targetY, 0],
  };
}

/* ── Rig: static (fixed camera, no animation) ── */

export interface StaticConfig {
  position?: [number, number, number];
  lookAt?: [number, number, number];
}

export function computeStatic(_progress: number, config: StaticConfig = {}): CameraState {
  return {
    position: config.position ?? [0, 3.2, 7.5],
    lookAt: config.lookAt ?? [0, 1.5, 0],
  };
}

/* ── Dispatch ── */

const RIG_DISPATCH: Record<
  CameraRigType,
  (progress: number, config?: any) => CameraState
> = {
  "fly-through": computeFlyThrough,
  orbit: computeOrbit,
  static: computeStatic,
};

export function computeCameraState(
  rig: CameraRigType,
  progress: number,
  config?: any,
): CameraState {
  return RIG_DISPATCH[rig](progress, config);
}
