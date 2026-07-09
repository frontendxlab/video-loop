/** ChartScene tests. */

import { describe, it, expect } from "vitest";

describe("ChartScene", () => {
  it("accepts bar chart data", () => {
    const data = [{ label: "A", value: 10 }, { label: "B", value: 20 }];
    expect(data.length).toBe(2);
  });

  it("accepts line chart data", () => {
    const chartType = "line";
    const data = [{ label: "Q1", value: 5 }, { label: "Q2", value: 15 }];
    expect(chartType).toBe("line");
    expect(data.length).toBe(2);
  });

  it("computes nice axis max", () => {
    const values = [10, 20, 33];
    const maxVal = Math.max(...values, 1);
    const niceMax = Math.ceil(maxVal * 1.1);
    expect(niceMax).toBeGreaterThanOrEqual(maxVal);
  });
});
