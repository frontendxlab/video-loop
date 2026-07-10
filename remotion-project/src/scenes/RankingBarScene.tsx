/**
 * RankingBarScene — 3D ranking bars with camera fly-through.
 *
 * Renders data-driven 3D bars with deterministic camera path, label
 * sprites, and design tokens. Uses shared Three.js foundation (hex,
 * addFullLights, useThreeScene, computeCameraState).
 *
 * ponytail: Text labels use CanvasTexture sprites — works at 1x resolution.
 * Could pre-render label textures at higher resolution for ultra-sharp renders.
 */

import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";
import { z } from "zod";
import * as THREE from "three";
import { colors, fonts, chart } from "../design-tokens";
import { hex, addFullLights, useThreeScene, computeCameraState } from "../components/three";
import type { CameraRigType, ThreeSceneHandle } from "../components/three";

/* ── Schema ── */

export const RankingBarItemSchema = z.object({
  rank: z.number().int().positive(),
  label: z.string().min(1),
  value: z.number().min(0),
  color: z.string().optional(),
});

export const RankingBarSceneSchema = z.object({
  type: z.literal("ranking-bar"),
  title: z.string().optional(),
  items: z.array(RankingBarItemSchema).min(2).max(20),
  duration: z.number().positive(),
  cameraPath: z.enum(["fly-through", "orbit", "static"]).optional().default("fly-through"),
  showValues: z.boolean().optional().default(true),
  sceneStartFrame: z.number().optional().default(0),
});

export type RankingBarItem = z.infer<typeof RankingBarItemSchema>;
export type RankingBarSceneProps = z.infer<typeof RankingBarSceneSchema>;

/* ── Constants ── */

const BAR_WIDTH = 0.5;
const BAR_DEPTH = 0.5;
const BAR_SPACING = 0.95;
const MAX_BAR_HEIGHT = 5.5;
const MIN_BAR_HEIGHT = 0.15;
const LABEL_Y_OFFSET = 0.5;
const VALUE_Y_OFFSET = 0.25;
const FLOOR_Y = -0.1;

/* ── Label sprite factory ── */

function makeTextSprite(
  text: string,
  color: string,
  bgColor: string,
  fontSize: number,
  canvasW: number,
  canvasH: number,
): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = canvasW;
  canvas.height = canvasH;
  const ctx = canvas.getContext("2d")!;

  ctx.clearRect(0, 0, canvasW, canvasH);

  const textMetrics = ctx.measureText(text);
  const tw = textMetrics.width;
  const pad = 16;
  const pillW = tw + pad * 2;
  const pillH = fontSize * 1.1;
  const pillX = (canvasW - pillW) / 2;
  const pillY = (canvasH - pillH) / 2;

  ctx.fillStyle = bgColor;
  ctx.beginPath();
  ctx.roundRect(pillX, pillY, pillW, pillH, 6);
  ctx.fill();

  ctx.font = `bold ${fontSize}px ${fonts.headingFamily}, sans-serif`;
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, canvasW / 2, canvasH / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;

  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false,
    sizeAttenuation: true,
  });

  const sprite = new THREE.Sprite(material);
  sprite.scale.set(2, 1, 1);
  return sprite;
}

/* ── Pure animation helpers (testable without Three.js) ── */

export function calcStaggerDelay(index: number, _total: number): number {
  return index * 4;
}

export function calcBarGrowProgress(frame: number, staggerDelay: number, fps: number): number {
  return spring({
    frame: Math.max(0, frame - staggerDelay),
    fps,
    config: { damping: 16, stiffness: 90, mass: 0.7 },
  });
}

export function calcBarHeight(value: number, maxValue: number, progress: number): number {
  const target = Math.min(MAX_BAR_HEIGHT, Math.max(MIN_BAR_HEIGHT, (value / maxValue) * MAX_BAR_HEIGHT));
  return interpolate(progress, [0, 1], [MIN_BAR_HEIGHT, target], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });
}

export function calcCameraX(progress: number): number {
  return interpolate(progress, [0, 1], [-3.5, 3.5], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });
}

export function calcOrbitAngle(progress: number): number {
  return interpolate(progress, [0, 1], [0, Math.PI * 2], {
    easing: Easing.inOut(Easing.cubic),
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });
}

export function calcTitleOpacity(frame: number, fps: number): number {
  const t = frame / fps;
  return interpolate(t, [0, 1.5], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateRight: "clamp",
  });
}

/* ── Scene handle type ── */

interface RankingBarHandle extends ThreeSceneHandle {
  barMeshes: THREE.Mesh[];
  barLabels: THREE.Sprite[];
  barValueLabels: THREE.Sprite[];
  maxValue: number;
  totalBars: number;
}

/* ── Scene setup factory ── */

function buildScene(
  canvas: HTMLCanvasElement,
  width: number,
  height: number,
  items: RankingBarItem[],
  showValues: boolean,
): RankingBarHandle {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(hex(colors.background));

  const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
  camera.position.set(0, 3.5, 8);
  camera.lookAt(0, 1.5, 0);

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: false });
  renderer.setSize(width, height);
  renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  addFullLights(scene);

  // Floor / stage
  const totalBars = items.length;
  const layoutWidth = (totalBars - 1) * BAR_SPACING + BAR_WIDTH;
  const floorGeo = new THREE.PlaneGeometry(layoutWidth + 2, 3);
  const floorMat = new THREE.MeshStandardMaterial({
    color: hex(colors.surface),
    metalness: 0.3,
    roughness: 0.7,
    transparent: true,
    opacity: 0.6,
    side: THREE.DoubleSide,
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, FLOOR_Y, 0);
  floor.receiveShadow = true;
  scene.add(floor);

  // Subtle grid on floor
  const gridHelper = new THREE.GridHelper(
    layoutWidth + 2,
    Math.round(layoutWidth + 2),
    hex(colors.textMuted),
    hex(colors.chromeBorder),
  );
  gridHelper.position.y = FLOOR_Y + 0.01;
  gridHelper.material.transparent = true;
  gridHelper.material.opacity = 0.25;
  scene.add(gridHelper);

  // Bars
  const barMeshes: THREE.Mesh[] = [];
  const barLabels: THREE.Sprite[] = [];
  const barValueLabels: THREE.Sprite[] = [];
  const maxValue = Math.max(...items.map((i) => i.value));
  const seriesColors = chart.series;

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const xPos = (i - (totalBars - 1) / 2) * BAR_SPACING;
    const barColor = item.color || seriesColors[i % seriesColors.length];

    // Bar body
    const geo = new THREE.BoxGeometry(BAR_WIDTH, MIN_BAR_HEIGHT, BAR_DEPTH);
    const mat = new THREE.MeshStandardMaterial({
      color: hex(barColor),
      metalness: 0.25,
      roughness: 0.45,
      envMapIntensity: 0.4,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(xPos, FLOOR_Y + MIN_BAR_HEIGHT / 2, 0);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    scene.add(mesh);
    barMeshes.push(mesh);

    // Top accent cap
    const capMat = new THREE.MeshStandardMaterial({
      color: hex(barColor),
      metalness: 0.5,
      roughness: 0.2,
    });
    const cap = new THREE.Mesh(
      new THREE.BoxGeometry(BAR_WIDTH * 0.85, 0.06, BAR_DEPTH * 0.85),
      capMat,
    );
    cap.position.set(0, 0, 0);
    cap.userData.isCap = true;
    mesh.add(cap);

    // Label sprite
    const labelSprite = makeTextSprite(
      item.label, colors.text, "rgba(15, 23, 42, 0.7)", 36, 512, 128,
    );
    labelSprite.position.set(xPos, FLOOR_Y + MIN_BAR_HEIGHT + LABEL_Y_OFFSET, 0);
    scene.add(labelSprite);
    barLabels.push(labelSprite);

    // Value label
    if (showValues) {
      const valStr = formatValue(item.value);
      const valSprite = makeTextSprite(
        valStr, colors.highlight, "rgba(15, 23, 42, 0.5)", 32, 256, 96,
      );
      valSprite.position.set(xPos, FLOOR_Y + MIN_BAR_HEIGHT + VALUE_Y_OFFSET, 0);
      valSprite.scale.set(1.2, 0.6, 1);
      scene.add(valSprite);
      barValueLabels.push(valSprite);
    }
  }

  return { scene, camera, renderer, barMeshes, barLabels, barValueLabels, maxValue, totalBars };
}

/** Format large values as compact strings. */
function formatValue(n: number): string {
  if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(1) + "B";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toLocaleString();
}

/* ── Component ── */

export const RankingBarScene: React.FC<RankingBarSceneProps> = ({
  title,
  items,
  cameraPath = "fly-through",
  showValues = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = calcTitleOpacity(frame, fps);

  const canvasRef = useThreeScene<RankingBarHandle>(
    (canvas, w, h) => buildScene(canvas, w, h, items, showValues),
    [items, showValues],
    (handle, _frame, fpts) => {
      const { scene, camera, renderer, barMeshes, barLabels, barValueLabels, maxValue, totalBars } = handle;

      const totalDuration = barMeshes.length * 4 + 60;

      for (let i = 0; i < barMeshes.length; i++) {
        const mesh = barMeshes[i];
        const staggerDelay = calcStaggerDelay(i, totalBars);
        const progress = calcBarGrowProgress(_frame, staggerDelay, fpts);
        const itemValue = items[i].value;
        const barHeight = calcBarHeight(itemValue, maxValue, progress);

        mesh.scale.y = barHeight / MIN_BAR_HEIGHT;
        mesh.position.y = FLOOR_Y + barHeight / 2;

        if (barLabels[i]) {
          barLabels[i].position.y = FLOOR_Y + barHeight + LABEL_Y_OFFSET;
        }
        if (showValues && barValueLabels[i]) {
          barValueLabels[i].position.y = FLOOR_Y + barHeight + VALUE_Y_OFFSET;
        }
      }

      // Camera movement
      const cameraStartFrame = Math.min(
        totalBars * 4 + 15,
        totalDuration - fpts * 2,
      );
      const cameraProgress = Math.max(0, Math.min(1,
        (_frame - cameraStartFrame) / (totalDuration - cameraStartFrame),
      ));

      const camState = computeCameraState(cameraPath as CameraRigType, cameraProgress);
      camera.position.set(...camState.position);
      camera.lookAt(...camState.lookAt);

      renderer.render(scene, camera);
    },
    frame,
    fps,
  );

  return (
    <AbsoluteFill style={{ background: colors.background }}>
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: "100%", display: "block" }}
      />
      {title && (
        <div
          style={{
            position: "absolute",
            top: "5%",
            left: 0,
            right: 0,
            textAlign: "center",
            opacity: titleOpacity,
            pointerEvents: "none",
          }}
        >
          <h1
            style={{
              fontFamily: fonts.heading,
              fontSize: 42,
              fontWeight: 700,
              color: colors.text,
              margin: 0,
              letterSpacing: "-0.5px",
              textShadow: "0 2px 16px rgba(0,0,0,0.5)",
            }}
          >
            {title}
          </h1>
        </div>
      )}
    </AbsoluteFill>
  );
};
