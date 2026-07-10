/**
 * Deterministic light setup factories for Three.js scenes.
 * Pure functions — no React deps.
 */

import * as THREE from "three";

/**
 * Standard 3-point lighting: ambient + key (front-right-top) + fill (left).
 * Used by Hero3DScene and general-purpose scenes.
 */
export function addStandardLights(scene: THREE.Scene): void {
  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const key = new THREE.DirectionalLight(0xffffff, 1.2);
  key.position.set(5, 10, 7);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x8888ff, 0.3);
  fill.position.set(-3, 0, 5);
  scene.add(fill);
}

/**
 * Full 4-point lighting: ambient + key (shadow-casting) + fill + rim.
 * Used by RankingBarScene and data-visualization scenes.
 */
export function addFullLights(scene: THREE.Scene): void {
  scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  const key = new THREE.DirectionalLight(0xffffff, 1.0);
  key.position.set(6, 12, 8);
  key.castShadow = true;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x8888ff, 0.3);
  fill.position.set(-4, 2, 6);
  scene.add(fill);
  const rim = new THREE.DirectionalLight(0xffffff, 0.15);
  rim.position.set(0, -2, -6);
  scene.add(rim);
}
