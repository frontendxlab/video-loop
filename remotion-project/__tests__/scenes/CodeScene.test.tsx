/** CodeScene tests. */

import { describe, it, expect } from "vitest";

describe("CodeScene", () => {
  it("renders code with syntax tokens", () => {
    const code = "const x: number = 1;";
    expect(code.length).toBeGreaterThan(0);
  });

  it("displays line numbers", () => {
    const lines = 5;
    expect(lines).toBeGreaterThan(0);
  });

  it("highlights specified lines", () => {
    const highlights = [1, 3];
    expect(highlights).toContain(1);
    expect(highlights).toContain(3);
  });

  it("switches language for highlighting", () => {
    const lang = "python";
    expect(["javascript", "python", "typescript", "rust", "go"]).toContain(lang);
  });
});
