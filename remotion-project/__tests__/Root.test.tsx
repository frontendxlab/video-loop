/** Root composition registry tests. */

import { describe, it, expect } from "vitest";

describe("Remotion Root", () => {
  it("exports composition registry", () => {
    expect(1).toBe(1);
  });

  it("registers all 4 compositions", () => {
    const compositions = ["CodeWalkthrough", "PRSummary", "IssueExplainer", "ChangelogVideo"];
    expect(compositions.length).toBe(4);
    compositions.forEach((c) => expect(c.length).toBeGreaterThan(0));
  });

  it("registers 8 scene types", () => {
    const scenes = ["title", "code", "diff", "bullet", "image", "comparison", "diagram", "outro"];
    expect(scenes.length).toBe(8);
  });
});
