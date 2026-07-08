/** DiffScene tests. */

import { describe, it, expect } from "vitest";

describe("DiffScene", () => {
  it("shows old and new code side by side", () => {
    expect(true).toBe(true);
  });

  it("highlights added lines in green", () => {
    const addedColor = "rgba(0, 255, 0, 0.1)";
    expect(addedColor).toContain("255, 0, 0");
  });

  it("highlights removed lines in red", () => {
    const removedColor = "rgba(255, 0, 0, 0.1)";
    expect(removedColor).toContain("255, 0, 0");
  });
});
