/**
 * R3F-based Three.js canvas wrapper with camera rig support.
 *
 * Use for declarative scenes (R3F components as children).
 * For imperative canvas-ref scenes, use `useThreeScene` hook instead.
 *
 * Example:
 * ```tsx
 * <ThreeScene cameraRig={{ type: "fly-through", progress: 0.5 }}>
 *   <mesh><boxGeometry args={[1,1,1]} /></mesh>
 * </ThreeScene>
 * ```
 */

import React, { useMemo } from "react";
import { ThreeCanvas } from "@remotion/three";
import { AbsoluteFill } from "remotion";
import { computeCameraState } from "./three-camera";
import type { CameraRigType } from "./three-types";

export interface ThreeSceneProps {
  readonly children: React.ReactNode;
  readonly width?: number;
  readonly height?: number;
  /** Manual camera override (takes precedence over cameraRig). */
  readonly camera?: Partial<React.ComponentProps<typeof ThreeCanvas>["camera"]>;
  /** Deterministic camera rig — computes position from progress [0,1]. */
  readonly cameraRig?: {
    type: CameraRigType;
    progress: number;
    config?: Record<string, unknown>;
  };
}

export const ThreeScene: React.FC<ThreeSceneProps> = ({
  children,
  width = 1920,
  height = 1080,
  camera,
  cameraRig,
}) => {
  const resolvedCamera = useMemo(() => {
    if (camera) return camera;
    if (cameraRig) {
      const state = computeCameraState(cameraRig.type, cameraRig.progress, cameraRig.config);
      return {
        position: state.position,
        lookAt: state.lookAt,
        fov: 35,
        near: 0.1,
        far: 100,
      };
    }
    return { position: [0, 0, 5], fov: 35, near: 0.1, far: 100 };
  }, [camera, cameraRig]);

  return (
    <AbsoluteFill>
      <ThreeCanvas width={width} height={height} camera={resolvedCamera}>
        <ambientLight intensity={0.4} />
        <directionalLight position={[10, 10, 10]} intensity={1} />
        <directionalLight position={[-5, -5, -5]} intensity={0.3} />
        {children}
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
