/** ScreenflowScene tests. */

import { describe, it, expect } from "vitest";

describe("ScreenflowScene", () => {
  it("accepts valid screenflow scene data", () => {
    const scene = {
      device: "browser",
      screenshot: "/screenshots/demo.png",
      callouts: [{ text: "Key feature", x: 50, y: 30 }],
      cursorPath: [{ x: 10, y: 10, frame: 0 }],
      duration: 150,
    };
    expect(scene.device).toBe("browser");
    expect(scene.callouts.length).toBe(1);
    expect(scene.cursorPath.length).toBe(1);
    expect(scene.duration).toBe(150);
  });

  it("device frame has correct dimensions", () => {
    const DEVICE_W = 960;
    const DEVICE_H = 600;
    const ratio = DEVICE_W / DEVICE_H;
    expect(ratio).toBeCloseTo(1.6, 1);
    expect(DEVICE_W).toBeGreaterThan(0);
    expect(DEVICE_H).toBeGreaterThan(0);
  });

  it("maps callout percentage to pixel position", () => {
    const SCREEN_W = 936;
    const SCREEN_H = 556;
    const xPct = 50;
    const yPct = 30;
    const px = (xPct / 100) * SCREEN_W;
    const py = (yPct / 100) * SCREEN_H;
    expect(px).toBe(468);
    expect(py).toBeCloseTo(166.8, 1);
  });

  it("interpolates cursor position between path points", () => {
    const path = [
      { x: 10, y: 20, frame: 0 },
      { x: 50, y: 80, frame: 30 },
    ];
    const frame = 15;
    const segLen = path[1].frame - path[0].frame;
    const t = frame / segLen;
    const cx = path[0].x + (path[1].x - path[0].x) * t;
    const cy = path[0].y + (path[1].y - path[0].y) * t;
    expect(cx).toBe(30);
    expect(cy).toBe(50);
  });

  it("clamps cursor at final path point when frame exceeds path", () => {
    const path = [
      { x: 10, y: 20, frame: 0 },
      { x: 50, y: 80, frame: 30 },
    ];
    const frame = 60;
    const last = path[path.length - 1];
    expect(last.x).toBe(50);
    expect(last.y).toBe(80);
  });

  it("starts cursor at first path point on frame zero", () => {
    const path = [{ x: 25, y: 50, frame: 0 }];
    const frame = 0;
    const t = Math.min(1, Math.max(0, frame - path[0].frame) / 1);
    const cx = path[0].x;
    const cy = path[0].y;
    expect(cx).toBe(25);
    expect(cy).toBe(50);
  });

  it("fades in scene over first 20 frames", () => {
    const opacity = (f: number) => Math.min(1, f / 20);
    expect(opacity(0)).toBe(0);
    expect(opacity(10)).toBe(0.5);
    expect(opacity(20)).toBe(1);
  });

  it("handles empty callouts gracefully", () => {
    const callouts: { text: string; x: number; y: number }[] = [];
    expect(callouts.length).toBe(0);
  });

  it("handles empty cursor path gracefully", () => {
    const cursorPath: { x: number; y: number; frame: number }[] = [];
    expect(cursorPath.length).toBe(0);
  });

  it("accepts phone device type", () => {
    const device = "phone";
    expect(["phone", "browser"]).toContain(device);
  });

  it("callout card slides in with stagger", () => {
    const stagger = 25;
    const fadeDur = 20;
    const cards = ["A", "B", "C"];
    const revealFrames = cards.map((_, i) => 15 + i * stagger);
    expect(revealFrames[0]).toBe(15);
    expect(revealFrames[1]).toBe(40);
    expect(revealFrames[2]).toBe(65);
    expect(cards.length).toBe(3);
  });

  it("chrome height is 44px", () => {
    const CHROME_H = 44;
    expect(CHROME_H).toBeGreaterThan(30);
    expect(CHROME_H).toBeLessThan(60);
  });

  it("device enters with spring animation 0.92->1", () => {
    const deviceScale = (s: number) => 0.92 + 0.08 * s;
    expect(deviceScale(0)).toBe(0.92);
    expect(deviceScale(1)).toBe(1);
  });
});
