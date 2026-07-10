/** Unit tests for shared Three.js type utilities. */

import { describe, it, expect } from "vitest";
import { hex, DEVICE_DIMS } from "../../../src/components/three/three-types";

describe("hex()", () => {
  it("converts #000000 to 0", () => {
    expect(hex("#000000")).toBe(0);
  });

  it("converts #FFFFFF to 16777215", () => {
    expect(hex("#FFFFFF")).toBe(16777215);
  });

  it("converts #FF0000 to 16711680", () => {
    expect(hex("#FF0000")).toBe(16711680);
  });

  it("converts #00FF00 to 65280", () => {
    expect(hex("#00FF00")).toBe(65280);
  });

  it("converts #0000FF to 255", () => {
    expect(hex("#0000FF")).toBe(255);
  });

  it("converts #4A90D9 consistently", () => {
    const result = hex("#4A90D9");
    expect(typeof result).toBe("number");
    expect(result).toBeGreaterThan(0);
  });
});

describe("DEVICE_DIMS", () => {
  it("has phone, laptop, monitor keys", () => {
    expect(Object.keys(DEVICE_DIMS)).toEqual(["phone", "laptop", "monitor"]);
  });

  it("phone has w > 0 and h > 0", () => {
    expect(DEVICE_DIMS.phone.w).toBeGreaterThan(0);
    expect(DEVICE_DIMS.phone.h).toBeGreaterThan(0);
  });

  it("laptop w > phone w", () => {
    expect(DEVICE_DIMS.laptop.w).toBeGreaterThan(DEVICE_DIMS.phone.w);
  });

  it("monitor w > laptop w", () => {
    expect(DEVICE_DIMS.monitor.w).toBeGreaterThan(DEVICE_DIMS.laptop.w);
  });

  it("inset is smaller than width for all devices", () => {
    for (const key of Object.keys(DEVICE_DIMS) as Array<keyof typeof DEVICE_DIMS>) {
      expect(DEVICE_DIMS[key].inset).toBeLessThan(DEVICE_DIMS[key].w);
    }
  });
});
