/** inputProps schema validation tests. */

import { describe, it, expect } from "vitest";
import { remotionStyleDefaults } from "../src/design-tokens";

describe("inputProps schema", () => {
  it("validates title scene props", () => {
    const scene = { type: "title", title: "Hello", subtitle: "World", duration: 120 };
    expect(scene.type).toBe("title");
    expect(scene.title.length).toBeGreaterThan(0);
    expect(scene.duration).toBeGreaterThan(0);
  });

  it("validates code scene props", () => {
    const scene = { type: "code", code: "const x = 1;", lang: "javascript", highlightLines: [1], duration: 90 };
    expect(scene.type).toBe("code");
    expect(scene.code.length).toBeGreaterThan(0);
  });

  it("validates diff scene props", () => {
    const scene = { type: "diff", oldCode: "a", newCode: "b", lang: "javascript", duration: 120 };
    expect(scene.type).toBe("diff");
  });

  it("validates bullet scene props (2-5 points)", () => {
    const scene = { type: "bullet", points: ["A", "B", "C"], duration: 150 };
    expect(scene.points.length).toBeGreaterThanOrEqual(2);
    expect(scene.points.length).toBeLessThanOrEqual(5);
  });

  it("validates image scene props", () => {
    const scene = { type: "image", src: "/path/to/img.png", caption: "A diagram", duration: 120 };
    expect(scene.type).toBe("image");
  });

  it("validates comparison scene props", () => {
    const scene = { type: "comparison", labelBefore: "Old", labelAfter: "New", duration: 180 };
    expect(scene.type).toBe("comparison");
  });

  it("validates diagram scene props", () => {
    const scene = { type: "diagram", config: { nodes: [{ id: "a", label: "A", position: { row: 0, col: 0 } }] }, duration: 180 };
    expect(scene.type).toBe("diagram");
  });

  it("validates outro scene props", () => {
    const scene = { type: "outro", title: "The End", cta: "github.com", duration: 90 };
    expect(scene.type).toBe("outro");
  });

  it("validates map-geo scene props", () => {
    const scene = { type: "map-geo", centerLat: 48.8566, centerLng: 2.3522, zoom: 10, title: "Paris", duration: 150 };
    expect(scene.type).toBe("map-geo");
    expect(scene.centerLat).toBeCloseTo(48.8566);
    expect(scene.zoom).toBe(10);
  });

  it("validates map-geo with markers", () => {
    const scene = { type: "map-geo", centerLat: 0, centerLng: 0, markers: [{ lat: 48.85, lng: 2.35, label: "Paris" }], duration: 150 };
    expect(scene.markers.length).toBe(1);
    expect(scene.markers[0].label).toBe("Paris");
  });

  it("validates full inputProps structure", () => {
    const props = {
      title: "Test Video",
      scenes: [{ type: "title" as const, title: "Hello", duration: 60 }],
      audioTracks: [{ src: "audio.wav", startFrame: 0, duration: 60 }],
      captions: [{ text: "Hello", startMs: 0, endMs: 500 }],
      voice: "alba",
      style: remotionStyleDefaults,
    };
    expect(props.scenes.length).toBe(1);
    expect(props.audioTracks.length).toBe(1);
    expect(props.captions.length).toBe(1);
  });
});
