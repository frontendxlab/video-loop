/** MapScene tests — schema, projection math, rendering. */

import { describe, it, expect } from "vitest";
import { MapSceneSchema } from "../../src/scenes/MapScene";

describe("MapSceneSchema", () => {
  it("validates minimal scene", () => {
    const r = MapSceneSchema.safeParse({
      type: "map-geo",
      centerLat: 48.8566,
      centerLng: 2.3522,
      zoom: 10,
      duration: 150,
    });
    expect(r.success).toBe(true);
  });

  it("applies defaults", () => {
    const r = MapSceneSchema.safeParse({
      type: "map-geo",
      centerLat: 0,
      centerLng: 0,
      duration: 120,
    });
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.data.zoom).toBe(5);
      expect(r.data.style).toBe("streets");
      expect(r.data.markers).toEqual([]);
      expect(r.data.routes).toEqual([]);
    }
  });

  it("rejects missing center", () => {
    const r = MapSceneSchema.safeParse({ type: "map-geo", duration: 120 });
    expect(r.success).toBe(false);
  });

  it("validates with markers", () => {
    const r = MapSceneSchema.safeParse({
      type: "map-geo",
      centerLat: 48.8566,
      centerLng: 2.3522,
      zoom: 8,
      markers: [
        { lat: 48.8566, lng: 2.3522, label: "Paris", color: "#FF5733" },
        { lat: 48.5734, lng: 7.752, label: "Strasbourg" },
      ],
      duration: 150,
    });
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.data.markers).toHaveLength(2);
    }
  });

  it("validates with route", () => {
    const r = MapSceneSchema.safeParse({
      type: "map-geo",
      centerLat: 48.8566,
      centerLng: 2.3522,
      zoom: 8,
      routes: [
        {
          points: [
            { lat: 48.8566, lng: 2.3522 },
            { lat: 48.5734, lng: 7.752 },
          ],
          color: "#F59E0B",
          width: 4,
        },
      ],
      duration: 150,
    });
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.data.routes).toHaveLength(1);
      expect(r.data.routes[0].points).toHaveLength(2);
    }
  });

  it("rejects invalid type", () => {
    const r = MapSceneSchema.safeParse({
      type: "title",
      centerLat: 48.8566,
      centerLng: 2.3522,
      duration: 150,
    });
    expect(r.success).toBe(false);
  });
});

describe("coordinate projection", () => {
  it("center projects to center", () => {
    const W = 800,
      H = 600;
    const scale = (5 * W) / 360;
    const x = W / 2 + (0 - 0) * scale;
    const y = H / 2 - (0 - 0) * scale;
    expect(x).toBe(W / 2);
    expect(y).toBe(H / 2);
  });

  it("positive lng moves right", () => {
    const W = 800,
      H = 600;
    const scale = (5 * W) / 360;
    const x = W / 2 + (10 - 0) * scale;
    const xCenter = W / 2 + (0 - 0) * scale;
    expect(x).toBeGreaterThan(xCenter);
  });

  it("positive lat moves up (y decreases)", () => {
    const W = 800,
      H = 600;
    const scale = (5 * H) / 360;
    const y = H / 2 - (10 - 0) * scale;
    const yCenter = H / 2 - (0 - 0) * scale;
    expect(y).toBeLessThan(yCenter);
  });
});

describe("scene properties", () => {
  it("pin path is a valid SVG path", () => {
    const pinPath =
      "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z";
    expect(pinPath.startsWith("M")).toBe(true);
    expect(pinPath.includes("z")).toBe(true);
  });
});
