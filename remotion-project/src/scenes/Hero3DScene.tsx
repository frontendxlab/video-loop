/**
 * Hero3DScene — device-rise 3D scene.
 *
 * Renders 3D device (phone/laptop/monitor) using Three.js that rises
 * from below with spring physics. Uses shared design tokens + Three.js
 * foundation (hex, addStandardLights, useThreeScene).
 *
 * ponytail: Three.js canvas renders at full res each frame; could
 * add OffscreenCanvas worker when perf demands it.
 */

import React, { useRef } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";
import { z } from "zod";
import * as THREE from "three";
import { colors, fonts } from "../design-tokens";
import { hex, DEVICE_DIMS, addStandardLights, useThreeScene } from "../components/three";
import type { DeviceType, ThreeSceneHandle } from "../components/three";

/* ── Schema ── */

export const Hero3DSceneSchema = z.object({
  type: z.literal("hero3d"),
  title: z.string(),
  subtitle: z.string().optional(),
  duration: z.number().positive(),
  deviceType: z.enum(["phone", "laptop", "monitor"]).optional().default("phone"),
  sceneStartFrame: z.number().optional().default(0),
});

export type Hero3DSceneProps = z.infer<typeof Hero3DSceneSchema>;

/* ── Scene handle type ── */

interface Hero3DHandle extends ThreeSceneHandle {
  device: THREE.Group;
}

/* ── Pure animation helpers (testable without Three.js) ── */

export function calcRiseProgress(frame: number, fps: number): number {
  return spring({ frame, fps, config: { damping: 14, stiffness: 70, mass: 0.8 } });
}

export function calcTilt(progress: number): number {
  return interpolate(progress, [0, 1], [0.5, 0.05], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });
}

export function calcScale(progress: number): number {
  return interpolate(progress, [0, 1], [0.7, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });
}

export function calcOverlayOpacity(progress: number): number {
  return interpolate(progress, [0, 0.5, 1], [0, 0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });
}

/* ── Device mesh builder (deterministic, called once) ── */

function buildDevice(deviceType: DeviceType): THREE.Group {
  const dims = DEVICE_DIMS[deviceType];
  const device = new THREE.Group();

  // Device body (bezel)
  const bodyGeo = new THREE.BoxGeometry(dims.w, dims.h, dims.d);
  const bodyMat = new THREE.MeshStandardMaterial({
    color: hex(colors.surface),
    metalness: 0.6,
    roughness: 0.3,
  });
  device.add(new THREE.Mesh(bodyGeo, bodyMat));

  // Screen (inset display area)
  const screenGeo = new THREE.PlaneGeometry(dims.w - dims.inset * 2, dims.h - dims.inset * 2);
  const screenMat = new THREE.MeshStandardMaterial({
    color: hex(colors.backgroundElevated),
    emissive: hex(colors.primary),
    emissiveIntensity: 0.06,
    metalness: 0.1,
    roughness: 0.9,
  });
  const screen = new THREE.Mesh(screenGeo, screenMat);
  screen.position.z = dims.d / 2 + 0.001;
  device.add(screen);

  // Chrome dots (macOS-style window controls) for laptop/monitor
  if (deviceType === "laptop" || deviceType === "monitor") {
    const dots = [
      { x: -dims.w / 2 + 0.15, y: dims.h / 2 - 0.12, color: hex(colors.chromeDotRed) },
      { x: -dims.w / 2 + 0.28, y: dims.h / 2 - 0.12, color: hex(colors.chromeDotYellow) },
      { x: -dims.w / 2 + 0.41, y: dims.h / 2 - 0.12, color: hex(colors.chromeDotGreen) },
    ];
    for (const dot of dots) {
      const g = new THREE.SphereGeometry(0.03, 8, 8);
      const m = new THREE.MeshStandardMaterial({ color: dot.color });
      const mesh = new THREE.Mesh(g, m);
      mesh.position.set(dot.x, dot.y, dims.d / 2 + 0.002);
      device.add(mesh);
    }
  }

  return device;
}

/* ── Scene setup factory (called once per canvas) ── */

function setupScene(
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
  deviceType: DeviceType,
): Hero3DHandle {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(1);

  addStandardLights(scene);

  const device = buildDevice(deviceType);
  scene.add(device);

  camera.position.set(0, 0.5, 4.8);
  camera.lookAt(0, 0, 0);

  return { scene, camera, renderer, device };
}

/* ── Component ── */

export const Hero3DScene: React.FC<Hero3DSceneProps> = ({
  title,
  subtitle,
  deviceType = "phone",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const riseProgressRef = useRef(0);

  riseProgressRef.current = calcRiseProgress(frame, fps);
  const riseProgress = riseProgressRef.current;
  const tilt = calcTilt(riseProgress);
  const scale = calcScale(riseProgress);
  const overlayOpacity = calcOverlayOpacity(riseProgress);

  const canvasRef = useThreeScene<Hero3DHandle>(
    (canvas, w, h) => setupScene(canvas, w, h, deviceType),
    [deviceType],
    (handle, _frame) => {
      const { device } = handle;

      // Rise: start below, move up to center
      device.position.y = interpolate(riseProgress, [0, 1], [-4.5, 0], {
        extrapolateRight: "clamp",
        extrapolateLeft: "clamp",
      });
      // Tilt: start angled back, end upright
      device.rotation.x = tilt;
      // Scale pop-in
      device.scale.set(scale, scale, scale);
    },
    frame,
    fps,
  );

  return (
    <AbsoluteFill style={{ background: colors.backgroundGradient }}>
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: "100%", display: "block" }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "12%",
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: overlayOpacity,
        }}
      >
        <h1
          style={{
            fontFamily: fonts.heading,
            fontSize: 52,
            fontWeight: 700,
            color: colors.text,
            margin: 0,
            letterSpacing: "-0.5px",
            lineHeight: 1.2,
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              fontFamily: fonts.sans,
              fontSize: 20,
              color: colors.textMuted,
              marginTop: 12,
              letterSpacing: 0.5,
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </AbsoluteFill>
  );
};
