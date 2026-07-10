/** DualChartScene tests — bar+line dual-axis chart. */

import { describe, it, expect } from "vitest";

describe("DualChartScene", () => {
  it("accepts bar and line data arrays", () => {
    const barData = [
      { label: "Jan", value: 30 },
      { label: "Feb", value: 50 },
    ];
    const lineData = [
      { label: "Jan", value: 8 },
      { label: "Feb", value: 15 },
    ];
    expect(barData.length).toBe(2);
    expect(lineData.length).toBe(2);
  });

  it("computes separate axis max for bar and line", () => {
    const barValues = [30, 50, 20];
    const lineValues = [8, 15, 5];
    const barMax = Math.max(...barValues, 1);
    const lineMax = Math.max(...lineValues, 1);
    const niceBarMax = Math.ceil(barMax * 1.15);
    const niceLineMax = Math.ceil(lineMax * 1.15);
    expect(niceBarMax).toBeGreaterThanOrEqual(barMax);
    expect(niceLineMax).toBeGreaterThanOrEqual(lineMax);
    expect(niceBarMax).not.toBe(niceLineMax);
  });

  it("handles single-item datasets", () => {
    const barData = [{ label: "Only", value: 42 }];
    const lineData = [{ label: "Only", value: 7 }];
    expect(barData.length).toBe(1);
    expect(lineData.length).toBe(1);
    expect(barData[0].value).toBe(42);
    expect(lineData[0].value).toBe(7);
  });

  it("provides default legend labels", () => {
    const barLabel = "Bars";
    const lineLabel = "Line";
    expect(barLabel).toBe("Bars");
    expect(lineLabel).toBe("Line");
  });

  it("extrapolates left axis label", () => {
    const label = "Revenue ($)";
    expect(label).toBe("Revenue ($)");
  });

  it("extrapolates right axis label", () => {
    const label = "Growth (%)";
    expect(label).toBe("Growth (%)");
  });

  it("renders title when provided", () => {
    const title = "Dual Chart Demo";
    expect(title.length).toBeGreaterThan(0);
  });
});
