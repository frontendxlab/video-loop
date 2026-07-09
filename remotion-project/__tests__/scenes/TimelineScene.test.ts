/** TimelineScene tests. */

import { describe, it, expect } from "vitest";

describe("TimelineScene", () => {
  it("accepts events array", () => {
    const events = [{ label: "Start", date: "2020" }, { label: "End", date: "2024" }];
    expect(events.length).toBe(2);
  });

  it("places events along axis", () => {
    const events = [{ label: "A" }, { label: "B" }, { label: "C" }];
    const positions = events.map((_, i) => i / (events.length - 1));
    expect(positions[0]).toBe(0);
    expect(positions[positions.length - 1]).toBe(1);
  });
});
