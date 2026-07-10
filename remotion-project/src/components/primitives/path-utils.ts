import { interpolate, Easing } from "remotion";

/* ─── SVG Path Command Types ─── */

export interface PathCommand {
  cmd: string;
  args: number[];
}

/* ─── Parse SVG path string to command array ─── */

export function parsePath(d: string): PathCommand[] {
  const re = /([MLCSTQAZ])\s*([-\d.,\s]*)/gi;
  const cmds: PathCommand[] = [];
  let match: RegExpExecArray | null;
  while ((match = re.exec(d.trim())) !== null) {
    const cmd = match[1].toUpperCase();
    const nums = (match[2] ?? "")
      .trim()
      .split(/[\s,]+/)
      .filter(Boolean)
      .map(Number);
    if (nums.length === 0) {
      cmds.push({ cmd, args: [] });
    } else {
      const argLen =
        cmd === "C" ? 6 :
        cmd === "S" || cmd === "Q" ? 4 :
        cmd === "T" || cmd === "L" || cmd === "M" ? 2 :
        cmd === "H" || cmd === "V" ? 1 :
        cmd === "A" ? 7 : 0;
      for (let i = 0; i < nums.length; i += argLen) {
        cmds.push({ cmd, args: nums.slice(i, i + argLen) });
      }
    }
  }
  return cmds;
}

/* ─── Serialize command array back to path string ─── */

export function stringifyPath(cmds: PathCommand[]): string {
  return cmds.map((c) => `${c.cmd} ${c.args.map((a) => a.toFixed(1)).join(" ")}`).join(" ");
}

/* ─── Interpolate between two paths (same structure required) ─── */

export function interpolatePaths(a: string, b: string, progress: number): string {
  const cmdsA = parsePath(a);
  const cmdsB = parsePath(b);
  const len = Math.min(cmdsA.length, cmdsB.length);
  const out: PathCommand[] = [];
  for (let i = 0; i < len; i++) {
    const ca = cmdsA[i];
    const cb = cmdsB[i];
    const cmd = ca.args.length > 0 ? ca.cmd : cb.cmd;
    const args = ca.args.map((va, j) => {
      const vb = cb.args[j] ?? va;
      return va + (vb - va) * progress;
    });
    out.push({ cmd, args });
  }
  return stringifyPath(out);
}

/* ─── Get stroke-dashoffset for draw animation ─── */

export interface DrawPathProps {
  strokeDasharray: number;
  strokeDashoffset: number;
}

export function getDrawPathProps(
  frame: number,
  durationInFrames: number,
  pathLength: number,
  options?: { easing?: (t: number) => number; delay?: number },
): DrawPathProps {
  const easing = options?.easing ?? Easing.inOut(Easing.cubic);
  const delay = options?.delay ?? 0;
  const progress = interpolate(frame, [delay, delay + durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing,
  });
  return {
    strokeDasharray: pathLength,
    strokeDashoffset: pathLength * (1 - progress),
  };
}

/* ─── Compute approximate SVG path length ─── */

export function estimatePathLength(d: string): number {
  const cmds = parsePath(d);
  let total = 0;
  let cx = 0;
  let cy = 0;
  for (const c of cmds) {
    const [x, y] = c.args;
    if (c.cmd === "M") {
      cx = x;
      cy = y;
    } else if (c.cmd === "L") {
      total += Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
      cx = x;
      cy = y;
    } else if (c.cmd === "C") {
      const [x1, y1, x2, y2, xe, ye] = c.args;
      total += Math.sqrt((xe - cx) ** 2 + (ye - cy) ** 2);
      cx = xe;
      cy = ye;
    }
  }
  return Math.max(total, 1);
}

/* ─── Showcase Patterns ─── */

export const SHOWCASE_PATTERNS: Record<string, { d: string; label: string }> = {
  wave: {
    label: "Wave",
    d: "M 100 400 C 300 100, 500 700, 700 400 C 900 100, 1100 700, 1300 400 C 1500 100, 1700 700, 1820 400",
  },
  sine: {
    label: "Sine",
    d: "M 100 540 Q 300 240, 500 540 T 900 540 T 1300 540 T 1700 540",
  },
  spiral: {
    label: "Spiral",
    d: "M 960 540 C 960 340, 760 340, 760 540 C 760 740, 1160 740, 1160 540 C 1160 240, 660 240, 660 540 C 660 840, 1260 840, 1260 540",
  },
  diamond: {
    label: "Diamond",
    d: "M 960 200 L 1300 540 L 960 880 L 620 540 Z",
  },
  hexagon: {
    label: "Hexagon",
    d: "M 960 200 L 1260 360 L 1260 640 L 960 800 L 660 640 L 660 360 Z",
  },
  grid3x3: {
    label: "3×3 Grid",
    d: "M 640 200 L 640 880 M 1280 200 L 1280 880 M 200 380 L 1720 380 M 200 700 L 1720 700",
  },
  cross: {
    label: "Cross",
    d: "M 860 200 L 860 880 M 1060 200 L 1060 880 M 200 440 L 1720 440 M 200 640 L 1720 640",
  },
  arrowRight: {
    label: "Arrow Right",
    d: "M 400 540 L 1520 540 M 1200 340 L 1520 540 L 1200 740",
  },
};
