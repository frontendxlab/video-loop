import { describe, it, expect } from "vitest";
import {
  parsePath,
  stringifyPath,
  interpolatePaths,
  getDrawPathProps,
  estimatePathLength,
  SHOWCASE_PATTERNS,
} from "../../src/components/primitives/path-utils";

describe("parsePath", () => {
  it("parses simple M L path", () => {
    const cmds = parsePath("M 10 20 L 30 40");
    expect(cmds).toEqual([
      { cmd: "M", args: [10, 20] },
      { cmd: "L", args: [30, 40] },
    ]);
  });

  it("parses cubic bezier", () => {
    const cmds = parsePath("M 0 0 C 10 20 30 40 50 60");
    expect(cmds).toEqual([
      { cmd: "M", args: [0, 0] },
      { cmd: "C", args: [10, 20, 30, 40, 50, 60] },
    ]);
  });

  it("handles Z command", () => {
    const cmds = parsePath("M 0 0 L 10 10 Z");
    expect(cmds[2]).toEqual({ cmd: "Z", args: [] });
  });

  it("handles empty string", () => {
    expect(parsePath("")).toEqual([]);
  });

  it("handles multiple M L pairs (polyline)", () => {
    const cmds = parsePath("M 100 200 L 300 400 L 500 600");
    expect(cmds).toHaveLength(3);
    expect(cmds[1].args).toEqual([300, 400]);
    expect(cmds[2].args).toEqual([500, 600]);
  });

  it("handles comma-separated args", () => {
    const cmds = parsePath("M 10,20 L 30,40");
    expect(cmds[0].args).toEqual([10, 20]);
    expect(cmds[1].args).toEqual([30, 40]);
  });
});

describe("stringifyPath", () => {
  it("round-trips simple path", () => {
    const d = "M 10 20 L 30 40";
    const cmds = parsePath(d);
    expect(stringifyPath(cmds)).toBe("M 10.0 20.0 L 30.0 40.0");
  });
});

describe("interpolatePaths", () => {
  it("interpolates between two lines at 50%", () => {
    const result = interpolatePaths("M 0 0 L 100 0", "M 0 0 L 200 0", 0.5);
    expect(result).toContain("50.0");
  });

  it("returns start at progress 0", () => {
    const result = interpolatePaths("M 10 20 L 30 40", "M 50 60 L 70 80", 0);
    expect(result).toBe("M 10.0 20.0 L 30.0 40.0");
  });

  it("returns end at progress 1", () => {
    const result = interpolatePaths("M 10 20 L 30 40", "M 50 60 L 70 80", 1);
    expect(result).toBe("M 50.0 60.0 L 70.0 80.0");
  });

  it("interpolates cubic bezier midpoints", () => {
    const result = interpolatePaths(
      "M 0 0 C 0 100 100 100 100 0",
      "M 0 0 C 0 200 200 200 200 0",
      0.5,
    );
    expect(result).toContain("M 0.0 0.0 C");
    expect(result).toContain("0.0");
    expect(result).toContain("150.0");
  });

  it("handles mismatched command count gracefully", () => {
    const result = interpolatePaths("M 0 0 L 100 0", "M 0 0", 0.5);
    expect(result).toBeTruthy();
  });
});

describe("getDrawPathProps", () => {
  it("returns full offset at frame 0", () => {
    const props = getDrawPathProps(0, 30, 100);
    expect(props.strokeDasharray).toBe(100);
    expect(props.strokeDashoffset).toBe(100);
  });

  it("returns zero offset after duration", () => {
    const props = getDrawPathProps(30, 30, 100);
    expect(props.strokeDashoffset).toBe(0);
  });

  it("respects delay", () => {
    const props = getDrawPathProps(0, 30, 100, { delay: 10 });
    expect(props.strokeDashoffset).toBe(100);
  });

  it("returns partial offset mid-animation", () => {
    const props = getDrawPathProps(15, 30, 200);
    expect(props.strokeDashoffset).toBeGreaterThan(0);
    expect(props.strokeDashoffset).toBeLessThan(200);
  });
});

describe("estimatePathLength", () => {
  it("returns positive length for a line", () => {
    const len = estimatePathLength("M 0 0 L 100 0");
    expect(len).toBe(100);
  });

  it("returns positive length for a cubic bezier", () => {
    const len = estimatePathLength("M 0 0 C 0 100 100 100 100 0");
    expect(len).toBeGreaterThan(0);
  });

  it("handles single M command", () => {
    const len = estimatePathLength("M 100 200");
    expect(len).toBe(1);
  });
});

describe("SHOWCASE_PATTERNS", () => {
  it("has at least 6 defined patterns", () => {
    expect(Object.keys(SHOWCASE_PATTERNS).length).toBeGreaterThanOrEqual(6);
  });

  it("every pattern has d and label", () => {
    for (const [key, val] of Object.entries(SHOWCASE_PATTERNS)) {
      expect(val.d).toBeTruthy();
      expect(val.label).toBeTruthy();
      expect(() => estimatePathLength(val.d)).not.toThrow();
    }
  });

  it("every pattern d is parseable", () => {
    for (const val of Object.values(SHOWCASE_PATTERNS)) {
      const cmds = parsePath(val.d);
      expect(cmds.length).toBeGreaterThan(0);
    }
  });
});
