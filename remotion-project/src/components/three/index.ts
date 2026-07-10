/**
 * Three.js foundation barrel — reusable scene base, camera rigs, lights, and lifecycle hook.
 *
 * Import from here for any new Three.js scene:
 * ```
 * import { hex, useThreeScene, addStandardLights, computeCameraState } from "../components/three";
 * ```
 */

export { type ThreeSceneHandle, type CameraRigType, type CameraState, type DeviceType, hex, DEVICE_DIMS } from "./three-types";
export { addStandardLights, addFullLights } from "./three-lights";
export { computeFlyThrough, computeOrbit, computeStatic, computeCameraState } from "./three-camera";
export { useThreeScene } from "./use-three-scene";
// ThreeScene (R3F) imported separately from "./ThreeScene" to avoid
// pulling @react-three/fiber into the shared foundation module tree.
