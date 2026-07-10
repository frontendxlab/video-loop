/** ParticleBackground: seeded RNG determinism, decorative bg rendering. */

import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import React from "react";
import {
  ParticleBackground,
  createSeededRng,
  hashString,
} from "../../src/components/ParticleBackground";

// Mock Remotion hooks (see sceneTokenAdoption.test.tsx for pattern)
vi.mock("remotion", () => ({
  useCurrentFrame: () => 0,
  AbsoluteFill: ({ style, children }: any) => <div style={style}>{children}</div>,
}));

// ---- Pure utility tests ----

describe("hashString", () => {
  it("returns same integer for identical input", () => {
    expect(hashString("hello")).toBe(hashString("hello"));
  });

  it("returns different values for different inputs", () => {
    expect(hashString("hello")).not.toBe(hashString("world"));
  });

  it("handles empty string", () => {
    expect(hashString("")).toBe(0);
  });
});

describe("createSeededRng", () => {
  it("produces identical sequence for same seed", () => {
    const a = createSeededRng("seed42");
    const b = createSeededRng("seed42");
    expect(Array.from({ length: 20 }, () => a())).toEqual(
      Array.from({ length: 20 }, () => b()),
    );
  });

  it("produces different sequence for different seed", () => {
    const a = createSeededRng("alpha");
    const b = createSeededRng("beta");
    expect(Array.from({ length: 10 }, () => a())).not.toEqual(
      Array.from({ length: 10 }, () => b()),
    );
  });

  it("returns values in [0, 1) range", () => {
    const rng = createSeededRng("range");
    for (let i = 0; i < 200; i++) {
      const v = rng();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it("same seed remains determinisic across multiple calls", () => {
    const rng = createSeededRng("persist-test");
    const first = rng();
    // advance many steps
    for (let i = 0; i < 1000; i++) rng();
    // fresh instance should match first value
    const rng2 = createSeededRng("persist-test");
    expect(rng2()).toBe(first);
  });
});

// ---- Component render tests ----

describe("ParticleBackground rendering", () => {
  it("renders SVG element", () => {
    const { container } = render(<ParticleBackground />);
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("renders requested number of particle circles", () => {
    const { container } = render(<ParticleBackground particleCount={10} />);
    const circles = container.querySelectorAll("circle");
    expect(circles.length).toBe(10);
  });

  it("renders zero particles when particleCount is 0", () => {
    const { container } = render(<ParticleBackground particleCount={0} />);
    expect(container.querySelectorAll("circle").length).toBe(0);
  });

  it("renders link lines when showLinks is true", () => {
    // Use high linkDistance to ensure at least some links form
    const { container } = render(
      <ParticleBackground particleCount={5} showLinks linkDistance={5000} />,
    );
    const lines = container.querySelectorAll("line");
    expect(lines.length).toBeGreaterThan(0);
  });

  it("omits link lines when showLinks is false", () => {
    const { container } = render(
      <ParticleBackground particleCount={10} showLinks={false} />,
    );
    expect(container.querySelectorAll("line").length).toBe(0);
  });

  it("applies masterOpacity to SVG element", () => {
    const { container } = render(<ParticleBackground masterOpacity={0.42} />);
    const svg = container.querySelector("svg");
    expect(svg?.style.opacity).toBe("0.42");
  });

  it("particle circles have fill color from design tokens", () => {
    const { container } = render(<ParticleBackground particleCount={3} />);
    const circles = container.querySelectorAll("circle");
    circles.forEach((c) => {
      // Should be a non-empty fill (not default black)
      expect(c.getAttribute("fill")).toBeTruthy();
      expect(c.getAttribute("fill")).not.toBe("#000000");
    });
  });

  it("deterministic seed produces identical output across renders", () => {
    // Render twice with same seed
    const { container: c1 } = render(
      <ParticleBackground seed="identical-test" particleCount={5} />,
    );
    const { container: c2 } = render(
      <ParticleBackground seed="identical-test" particleCount={5} />,
    );
    const circles1 = c1.querySelectorAll("circle");
    const circles2 = c2.querySelectorAll("circle");

    expect(circles1.length).toBe(circles2.length);
    circles1.forEach((c, i) => {
      expect(c.getAttribute("cx")).toBe(circles2[i].getAttribute("cx"));
      expect(c.getAttribute("cy")).toBe(circles2[i].getAttribute("cy"));
      expect(c.getAttribute("r")).toBe(circles2[i].getAttribute("r"));
    });
  });

  it("different seeds produce different particle positions", () => {
    const { container: c1 } = render(
      <ParticleBackground seed="seed-A" particleCount={20} />,
    );
    const { container: c2 } = render(
      <ParticleBackground seed="seed-B" particleCount={20} />,
    );
    const circles1 = c1.querySelectorAll("circle");
    const circles2 = c2.querySelectorAll("circle");

    // At least some positions differ (statistically certain with 20 particles)
    const anyDiff = Array.from(circles1).some(
      (c, i) =>
        c.getAttribute("cx") !== circles2[i].getAttribute("cx") ||
        c.getAttribute("cy") !== circles2[i].getAttribute("cy"),
    );
    expect(anyDiff).toBe(true);
  });

  it("applies frameOffset to shift positions", () => {
    // With frame=0 (mocked), frameOffset=100 should produce different positions
    // since speedX/Y * frameOffset changes positions
    const { container: c1 } = render(
      <ParticleBackground seed="offset" particleCount={10} frameOffset={0} />,
    );
    const { container: c2 } = render(
      <ParticleBackground seed="offset" particleCount={10} frameOffset={100} />,
    );
    const circles1 = c1.querySelectorAll("circle");
    const circles2 = c2.querySelectorAll("circle");

    // With non-zero speed and high frameOffset, positions differ
    const anyDiff = Array.from(circles1).some(
      (c, i) =>
        c.getAttribute("cx") !== circles2[i].getAttribute("cx") ||
        c.getAttribute("cy") !== circles2[i].getAttribute("cy"),
    );
    expect(anyDiff).toBe(true);
  });

  it("wraps particles within SVG bounds", () => {
    const { container } = render(
      <ParticleBackground
        seed="wrap-test"
        particleCount={5}
        width={1920}
        height={1080}
        frameOffset={9999}
      />,
    );
    const circles = container.querySelectorAll("circle");
    circles.forEach((c) => {
      const cx = Number(c.getAttribute("cx"));
      const cy = Number(c.getAttribute("cy"));
      expect(cx).toBeGreaterThanOrEqual(0);
      expect(cx).toBeLessThanOrEqual(1920);
      expect(cy).toBeGreaterThanOrEqual(0);
      expect(cy).toBeLessThanOrEqual(1080);
    });
  });

  it("svg has pointerEvents set to none", () => {
    const { container } = render(<ParticleBackground />);
    const svg = container.querySelector("svg");
    expect(svg?.style.pointerEvents).toBe("none");
  });
});
