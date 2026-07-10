import type { VintageParams, MagnifierMap } from "./composite";

/**
 * Deterministic pseudo-noise using pixel position + frame.
 * Sin-hash pattern — reliable across JS engines, shader-standard.
 */
function detNoise(x: number, y: number, frame: number): number {
  const s = Math.sin(x * 12.9898 + y * 78.233 + frame * 45.164) * 43758.5453;
  return s - Math.floor(s);
}

/** Clamp byte value. */
function clamp(v: number): number {
  return v < 0 ? 0 : v > 255 ? 255 : v;
}

/**
 * Apply glitch effect: per-row horizontal slice offset.
 * Pixels shifted off-edge become black.
 */
export function applyGlitch(
  data: Uint8ClampedArray,
  w: number,
  h: number,
  offsets: number[],
): Uint8ClampedArray {
  const out = new Uint8ClampedArray(data.length);
  for (let y = 0; y < h; y++) {
    const off = offsets[y] ?? 0;
    const rowStart = y * w * 4;
    for (let x = 0; x < w; x++) {
      const sx = x + off;
      const si = rowStart + x * 4;
      const di = rowStart + (sx >= 0 && sx < w ? sx * 4 : -4);
      if (sx >= 0 && sx < w) {
        out[di] = data[si];
        out[di + 1] = data[si + 1];
        out[di + 2] = data[si + 2];
        out[di + 3] = data[si + 3];
      }
    }
  }
  return out;
}

/**
 * Apply vintage effect: sepia matrix + deterministic grain + vignette.
 * Returns new Uint8ClampedArray.
 */
export function applyVintage(
  data: Uint8ClampedArray,
  w: number,
  h: number,
  params: VintageParams,
  frame: number,
): Uint8ClampedArray {
  const out = new Uint8ClampedArray(data.length);
  const { sepiaMatrix, grainNoise, vignetteAlpha } = params;
  const cx = w / 2;
  const cy = h / 2;
  const maxDist = Math.sqrt(cx * cx + cy * cy);

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    const px = (i / 4) % w;
    const py = Math.floor(i / 4 / w);

    // Sepia
    out[i] = clamp(r * sepiaMatrix[0][0] + g * sepiaMatrix[0][1] + b * sepiaMatrix[0][2]);
    out[i + 1] = clamp(r * sepiaMatrix[1][0] + g * sepiaMatrix[1][1] + b * sepiaMatrix[1][2]);
    out[i + 2] = clamp(r * sepiaMatrix[2][0] + g * sepiaMatrix[2][1] + b * sepiaMatrix[2][2]);

    // Deterministic grain
    if (grainNoise > 0) {
      const noise = (detNoise(px, py, frame) - 0.5) * grainNoise * 255;
      out[i] = clamp(out[i] + noise);
      out[i + 1] = clamp(out[i + 1] + noise);
      out[i + 2] = clamp(out[i + 2] + noise);
    }

    // Vignette
    const dist = Math.sqrt((px - cx) ** 2 + (py - cy) ** 2) / maxDist;
    const vigFactor = 1 - (1 - vignetteAlpha) * dist * dist;
    out[i] = clamp(out[i] * vigFactor);
    out[i + 1] = clamp(out[i + 1] * vigFactor);
    out[i + 2] = clamp(out[i + 2] * vigFactor);

    out[i + 3] = data[i + 3];
  }
  return out;
}

/**
 * Apply magnifier: displace pixels toward centre within radius.
 * Returns new Uint8ClampedArray.
 */
export function applyMagnifier(
  data: Uint8ClampedArray,
  w: number,
  h: number,
  map: MagnifierMap,
): Uint8ClampedArray {
  const out = new Uint8ClampedArray(data.length);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const { dx, dy } = map[y][x];
      const sx = x + dx;
      const sy = y + dy;
      const di = (y * w + x) * 4;
      if (sx >= 0 && sx < w && sy >= 0 && sy < h) {
        const si = (sy * w + sx) * 4;
        out[di] = data[si];
        out[di + 1] = data[si + 1];
        out[di + 2] = data[si + 2];
        out[di + 3] = data[si + 3];
      } else {
        out[di] = 0;
        out[di + 1] = 0;
        out[di + 2] = 0;
        out[di + 3] = 255;
      }
    }
  }
  return out;
}

/**
 * Return pixel data for a text render at given dimensions.
 * Uses OffscreenCanvas to rasterise styled text.
 */
export function renderTextContent(
  title: string,
  subtitle: string | undefined,
  w: number,
  h: number,
  bgGradient: string,
  textColor: string,
  accentColor: string,
  fontFamily: string,
): Uint8ClampedArray {
  if (typeof OffscreenCanvas === "undefined") {
    return new Uint8ClampedArray(w * h * 4);
  }
  const canvas = new OffscreenCanvas(w, h);
  const ctx = canvas.getContext("2d")!;

  const grad = ctx.createLinearGradient(0, 0, w, h);
  const parts = bgGradient.match(/#[0-9a-fA-F]{6}/g);
  grad.addColorStop(0, parts?.[0] ?? "#0F172A");
  grad.addColorStop(1, parts?.[1] ?? "#1E293B");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = textColor;
  const titleSize = subtitle ? 56 : 64;
  ctx.font = `700 ${titleSize}px ${fontFamily}`;
  ctx.fillText(title, w / 2, h / 2 - (subtitle ? 30 : 0));

  ctx.fillStyle = accentColor;
  ctx.fillRect(w / 2 - 30, h / 2 + 4, 60, 4);

  if (subtitle) {
    ctx.fillStyle = "rgba(229, 238, 248, 0.65)";
    ctx.font = `400 22px ${fontFamily}`;
    ctx.fillText(subtitle, w / 2, h / 2 + 56);
  }

  return ctx.getImageData(0, 0, w, h).data;
}
