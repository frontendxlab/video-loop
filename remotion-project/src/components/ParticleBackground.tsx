import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";
import { colors } from "../design-tokens";

// ---- Seeded PRNG (mulberry32) ----

/** Convert string to 32-bit integer hash (djb2). Deterministic. */
export function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h) + s.charCodeAt(i);
    h |= 0;
  }
  return h;
}

/** Create deterministic PRNG from string seed. Returns fns producing [0, 1) values. */
export function createSeededRng(seed: string): () => number {
  let s = hashString(seed) | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---- Types ----

interface ParticleDef {
  x: number;
  y: number;
  size: number;
  speedX: number;
  speedY: number;
  baseOpacity: number;
  color: string;
}

interface PositionedParticle extends ParticleDef {
  x: number;
  y: number;
}

interface ParticleBackgroundProps {
  /** Number of floating particles (default 50). */
  particleCount?: number;
  /** Speed multiplier (default 1). */
  speed?: number;
  /** Master opacity for entire SVG layer (default 0.6). */
  masterOpacity?: number;
  /** Color palette for particles. Defaults to token accent colors. */
  particleColors?: readonly string[];
  /** Seed for deterministic particle layout (default "particle-bg-default"). */
  seed?: string;
  /** Minimum particle radius in px (default 2). */
  minSize?: number;
  /** Maximum particle radius in px (default 6). */
  maxSize?: number;
  /** Canvas width in px (default 1920). */
  width?: number;
  /** Canvas height in px (default 1080). */
  height?: number;
  /** Max distance for link lines in px (default 120). */
  linkDistance?: number;
  /** Show connection lines between nearby particles (default true). */
  showLinks?: boolean;
  /** Opacity scalar for link lines (default 0.08). */
  linkOpacity?: number;
  /** Frame offset to shift animation phase without changing seed (default 0). */
  frameOffset?: number;
}

// ---- Default colors from design tokens ----

const DEFAULT_COLORS: readonly string[] = [
  colors.primary,
  colors.secondary,
  colors.accent,
  colors.highlight,
];

// ---- Component ----

export const ParticleBackground: React.FC<ParticleBackgroundProps> = ({
  particleCount = 50,
  speed = 1,
  masterOpacity = 0.6,
  particleColors,
  seed = "particle-bg-default",
  minSize = 2,
  maxSize = 6,
  width = 1920,
  height = 1080,
  linkDistance = 120,
  showLinks = true,
  linkOpacity = 0.08,
  frameOffset = 0,
}) => {
  const frame = useCurrentFrame();
  const currentFrame = frame + frameOffset;

  // Generate deterministic particle definitions once per seed change
  const particleDefs: ParticleDef[] = useMemo(() => {
    const rng = createSeededRng(seed);
    const pColors = particleColors ?? DEFAULT_COLORS;
    return Array.from({ length: particleCount }, () => ({
      x: rng() * width,
      y: rng() * height,
      size: minSize + rng() * (maxSize - minSize),
      speedX: (rng() - 0.5) * 0.8 * speed,
      speedY: (rng() - 0.5) * 0.8 * speed,
      baseOpacity: 0.3 + rng() * 0.7,
      color: pColors[Math.floor(rng() * pColors.length)],
    }));
    // ponytail: flat 1-layer particles. add z-layers with parallax speed tiers when depth needed.
    // ponytail: no audio reactivity. add amplitude modulation when music-synced scenes exist.
  }, [seed, particleCount, minSize, maxSize, speed, width, height, particleColors]);

  // Compute animated positions wrapping at edges
  const positioned: PositionedParticle[] = useMemo(() => {
    return particleDefs.map((p) => {
      let x = p.x + p.speedX * currentFrame;
      let y = p.y + p.speedY * currentFrame;
      x = ((x % width) + width) % width;
      y = ((y % height) + height) % height;
      return { ...p, x, y };
    });
  }, [particleDefs, currentFrame, width, height]);

  // Compute link lines between particles within linkDistance
  // ponytail: O(n²) — fine for ≤200 particles. spatial hash when count grows.
  const links: Array<[number, number, number]> = useMemo(() => {
    if (!showLinks || positioned.length < 2) return [];
    const result: Array<[number, number, number]> = [];
    for (let i = 0; i < positioned.length - 1; i++) {
      for (let j = i + 1; j < positioned.length; j++) {
        const a = positioned[i];
        const b = positioned[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < linkDistance) {
          result.push([i, j, dist]);
        }
      }
    }
    return result;
  }, [positioned, linkDistance, showLinks]);

  return (
    <svg
      width={width}
      height={height}
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        opacity: masterOpacity,
      }}
    >
      <defs>
        {/* ponytail: no glow/blur filter. add <filter> with feGaussianBlur for soft particles when cinematic glow needed. */}
      </defs>
      {showLinks && links.map(([i, j, dist]) => {
        const a = positioned[i];
        const b = positioned[j];
        const alpha = (1 - dist / linkDistance) * linkOpacity;
        return (
          <line
            key={`l-${i}-${j}`}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke={a.color}
            strokeWidth={0.5}
            opacity={alpha}
          />
        );
      })}
      {positioned.map((p, i) => (
        <circle
          key={`p-${i}`}
          cx={p.x}
          cy={p.y}
          r={p.size}
          fill={p.color}
          opacity={p.baseOpacity}
        />
      ))}
    </svg>
  );
};
