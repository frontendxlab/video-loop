/**
 * useThreeScene — hook for imperative Three.js canvas lifecycle.
 *
 * Manages setup/teardown of a WebGLRenderer + scene + camera, and
 * drives per-frame rendering. Consumers supply a `setup` factory and
 * an `animate` callback.
 *
 * Pattern:
 * ```
 * const canvasRef = useThreeScene(setupFn, [deps], animateFn, frame, fps);
 * <canvas ref={canvasRef} style={{ width: "100%", height: "100%", display: "block" }} />
 * ```
 */

import { useEffect, useRef } from "react";
import { useVideoConfig } from "remotion";
import type { ThreeSceneHandle } from "./three-types";

export function useThreeScene<T extends ThreeSceneHandle>(
  setup: (canvas: HTMLCanvasElement, width: number, height: number) => T,
  deps: React.DependencyList,
  animate: (handle: T, frame: number, fps: number) => void,
  frame: number,
  fps: number,
): React.RefObject<HTMLCanvasElement | null> {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const sceneRef = useRef<T | null>(null);
  const { width, height } = useVideoConfig();

  // Setup scene once or when deps change
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const handle = setup(canvas, width, height);
    sceneRef.current = handle;
    return () => {
      handle.renderer.dispose();
      sceneRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [width, height, ...deps]);

  // Per-frame render
  useEffect(() => {
    const s = sceneRef.current;
    if (!s) return;
    animate(s, frame, fps);
  });

  return canvasRef;
}
