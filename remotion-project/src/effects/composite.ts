import type {
  EffectLayer,
  GlitchConfig,
  MagnifierConfig,
  VintageConfig,
} from "./types";

/** Per-row horizontal offset for glitch distortion. */
export function computeGlitchOffsets(
  height: number,
  config: GlitchConfig,
  frame: number,
): number[] {
  const offsets: number[] = [];
  for (let y = 0; y < height; y++) {
    const scanBand = Math.floor((y / height) * config.scanlineCount);
    const wave = Math.sin(scanBand * 0.5 + frame * 0.3) * config.offsetMax * config.intensity;
    offsets.push(Math.round(wave));
  }
  return offsets;
}

/** Vintage colour-transformation parameters (sepia matrix + grain + vignette). */
export function computeVintageParams(config: VintageConfig) {
  const m = config.sepiaMix;
  const a = 1 - m;
  return {
    sepiaMatrix: [
      [0.393 + 0.607 * a, 0.769 - 0.769 * a, 0.189 - 0.189 * a] as const,
      [0.349 - 0.349 * a, 0.686 + 0.314 * a, 0.168 - 0.168 * a] as const,
      [0.272 - 0.272 * a, 0.534 - 0.534 * a, 0.131 + 0.869 * a] as const,
    ] as const,
    grainNoise: config.grainIntensity,
    vignetteAlpha: 1 - config.vignetteStrength,
  };
}

export type VintageParams = ReturnType<typeof computeVintageParams>;

/** Displacement map for magnifier lens. Outer (dx,dy) per pixel. */
export function computeMagnifierDisplacement(
  width: number,
  height: number,
  config: MagnifierConfig,
): { dx: number; dy: number }[][] {
  const cx = config.centerX * width;
  const cy = config.centerY * height;
  const r = config.radius;
  const zoom = config.zoom;
  const map: { dx: number; dy: number }[][] = [];

  for (let y = 0; y < height; y++) {
    const row: { dx: number; dy: number }[] = [];
    for (let x = 0; x < width; x++) {
      const dx = x - cx;
      const dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < r) {
        const t = dist / r; // 0 at centre, 1 at edge
        const scale = 1 - (1 - 1 / zoom) * (1 - t);
        row.push({
          dx: Math.round((x - cx) * (scale - 1)) || 0,
          dy: Math.round((y - cy) * (scale - 1)) || 0,
        });
      } else {
        row.push({ dx: 0, dy: 0 });
      }
    }
    map.push(row);
  }
  return map;
}

export type MagnifierMap = ReturnType<typeof computeMagnifierDisplacement>;

/** Composite multiple effect layers into one render config. */
export function compositeEffects(
  layers: EffectLayer[],
  width: number,
  height: number,
  frame: number,
): {
  glitchOffsets?: number[];
  vintageParams?: VintageParams;
  magnifierMap?: MagnifierMap;
} {
  const result: ReturnType<typeof compositeEffects> = {};

  for (const layer of layers) {
    switch (layer.type) {
      case "glitch":
        result.glitchOffsets = computeGlitchOffsets(height, layer as GlitchConfig, frame);
        break;
      case "vintage":
        result.vintageParams = computeVintageParams(layer as VintageConfig);
        break;
      case "magnifier":
        result.magnifierMap = computeMagnifierDisplacement(width, height, layer as MagnifierConfig);
        break;
    }
  }

  return result;
}
