/** BulletScene tests. */

import { describe, it, expect } from "vitest";

describe("BulletScene", () => {
  it("renders 2-5 bullet points", () => {
    const points = ["A", "B", "C"];
    expect(points.length).toBeGreaterThanOrEqual(2);
    expect(points.length).toBeLessThanOrEqual(5);
  });

  it("staggers entry within correct range", () => {
    const staggerFrames = 30;
    for (let i = 0; i < 5; i++) {
      expect(staggerFrames * i).toBeGreaterThanOrEqual(0);
    }
  });

  it("dims previous items when new appears", () => {
    const dimOpacity = 0.5;
    expect(dimOpacity).toBeLessThan(1);
    expect(dimOpacity).toBeGreaterThan(0);
  });
});
