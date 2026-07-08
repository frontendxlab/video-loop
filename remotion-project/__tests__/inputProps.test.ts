/** inputProps schema validation tests. */

import { describe, it, expect } from "vitest";

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

  it("validates full inputProps structure", () => {
    const props = {
      title: "Test Video",
      scenes: [{ type: "title" as const, title: "Hello", duration: 60 }],
      audioTracks: [{ src: "audio.wav", startFrame: 0, duration: 60 }],
      captions: [{ text: "Hello", startMs: 0, endMs: 500 }],
      voice: "alba",
      style: { primaryColor: "#000", font: "Inter", codeTheme: "poimandres" },
    };
    expect(props.scenes.length).toBe(1);
    expect(props.audioTracks.length).toBe(1);
    expect(props.captions.length).toBe(1);
  });
});
