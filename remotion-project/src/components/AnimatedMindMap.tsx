import React, { useMemo } from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { WordTiming, getStepProgress } from "../timing/audio-timing";

export interface MindMapNode {
  id: string;
  label: string;
  sublabel?: string;
  children: MindMapNode[];
  timing?: { startMs: number; endMs: number };
  color?: string;
}

interface AnimatedMindMapProps {
  root: MindMapNode;
  wordTimestamps: WordTiming[];
  sceneStartFrame: number;
  fps?: number;
}

const NODE_WIDTH = 160;
const NODE_HEIGHT = 60;
const H_GAP = 30;
const V_GAP = 80;
const PADDING = 60;
const ANIM_FRAMES = 20;

function subtreeWidth(node: MindMapNode): number {
  if (node.children.length === 0) return NODE_WIDTH;
  const cw = node.children.reduce((s, c) => s + subtreeWidth(c), 0);
  const gaps = (node.children.length - 1) * H_GAP;
  return Math.max(NODE_WIDTH, cw + gaps);
}

function assignPositions(
  node: MindMapNode,
  depth: number,
  left: number,
  map: Map<string, { x: number; y: number }>,
) {
  const sw = subtreeWidth(node);
  const cx = left + sw / 2;
  map.set(node.id, { x: cx, y: depth * (NODE_HEIGHT + V_GAP) + NODE_HEIGHT / 2 });

  if (node.children.length === 0) return;

  const widths = node.children.map(subtreeWidth);
  const total = widths.reduce((a, b) => a + b, 0);
  const gaps = (node.children.length - 1) * H_GAP;
  const blockW = total + gaps;
  let childLeft = left + (sw - blockW) / 2;

  for (let i = 0; i < node.children.length; i++) {
    assignPositions(node.children[i], depth + 1, childLeft, map);
    childLeft += widths[i] + H_GAP;
  }
}

function flattenBFS(root: MindMapNode): MindMapNode[] {
  const result: MindMapNode[] = [];
  const queue = [root];
  while (queue.length > 0) {
    const n = queue.shift()!;
    result.push(n);
    for (const c of n.children) queue.push(c);
  }
  return result;
}

function connectionPath(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
): string {
  const my = (y1 + y2) / 2;
  return `M ${x1} ${y1 + NODE_HEIGHT / 2} C ${x1} ${my}, ${x2} ${my}, ${x2} ${y2 - NODE_HEIGHT / 2}`;
}

const COLORS = ["#6C63FF", "#FF6584", "#58A6FF", "#3FB950", "#D29922", "#FF6B6B"];

export const AnimatedMindMap: React.FC<AnimatedMindMapProps> = ({
  root,
  wordTimestamps,
  sceneStartFrame,
  fps: propFps,
}) => {
  const frame = useCurrentFrame();
  const { fps: configFps } = useVideoConfig();
  const fps = propFps ?? configFps;

  const positions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    assignPositions(root, 0, 0, map);
    return map;
  }, [root]);

  const allNodes = useMemo(() => flattenBFS(root), [root]);

  const maxX = Math.max(...Array.from(positions.values()).map((p) => p.x), NODE_WIDTH);
  const maxY = Math.max(...Array.from(positions.values()).map((p) => p.y), NODE_HEIGHT);
  const svgW = maxX + NODE_WIDTH / 2 + PADDING * 2;
  const svgH = maxY + NODE_HEIGHT / 2 + PADDING * 2;

  const hasTiming = wordTimestamps.length > 0;

  const wordsPerNode = hasTiming
    ? Math.max(1, Math.floor(wordTimestamps.length / allNodes.length))
    : 0;

  function getProgress(node: MindMapNode, idx: number): number {
    if (hasTiming) {
      if (node.timing) {
        return getStepProgress(frame, fps, node.timing.startMs, node.timing.endMs, sceneStartFrame);
      }
      const wordIdx = Math.min(idx * wordsPerNode, wordTimestamps.length - 1);
      const w = wordTimestamps[wordIdx];
      if (!w) return 1;
      return getStepProgress(frame, fps, w.startMs, w.endMs, sceneStartFrame);
    }
    const staggerDelay = idx * 8;
    const local = frame - sceneStartFrame - staggerDelay;
    if (local < 0) return 0;
    if (local >= ANIM_FRAMES) return 1;
    return local / ANIM_FRAMES;
  }

  const connections: { from: string; to: string }[] = [];
  function collectEdges(n: MindMapNode) {
    for (const c of n.children) {
      connections.push({ from: n.id, to: c.id });
      collectEdges(c);
    }
  }
  collectEdges(root);

  const offsetX = PADDING;
  const offsetY = PADDING;

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%)",
        width: "100%",
        height: "100%",
        overflow: "hidden",
      }}
    >
      <svg
        width={svgW}
        height={svgH}
        viewBox={`0 0 ${svgW} ${svgH}`}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {connections.map(({ from, to }) => {
          const p1 = positions.get(from);
          const p2 = positions.get(to);
          if (!p1 || !p2) return null;
          const childIdx = allNodes.findIndex((n) => n.id === to);
          const childNode = allNodes[childIdx];
          const prog = childNode ? getProgress(childNode, childIdx) : 1;
          const x1 = p1.x + offsetX;
          const y1 = p1.y + offsetY;
          const x2 = p2.x + offsetX;
          const y2 = p2.y + offsetY;
          const path = connectionPath(x1, y1, x2, y2);
          const pathLen = path.length * 3;
          return (
            <path
              key={`conn-${from}-${to}`}
              d={path}
              fill="none"
              stroke="rgba(255,255,255,0.25)"
              strokeWidth={2}
              strokeDasharray={pathLen}
              strokeDashoffset={pathLen * (1 - prog * 0.8)}
              filter="url(#glow)"
              style={{ transition: "stroke-dashoffset 0.1s linear" }}
            />
          );
        })}
      </svg>

      {allNodes.map((node, idx) => {
        const pos = positions.get(node.id);
        if (!pos) return null;
        const prog = getProgress(node, idx);
        const virtualFrame = prog * ANIM_FRAMES;
        const s = spring({
          frame: virtualFrame,
          fps: 30,
          config: { damping: 14, stiffness: 90 },
        });
        const opacity = interpolate(virtualFrame, [0, ANIM_FRAMES], [0, 1], {
          extrapolateRight: "clamp",
        });
        const colorIdx = allNodes.indexOf(node) % COLORS.length;
        const accentColor = node.color ?? COLORS[colorIdx];
        const x = pos.x + offsetX - NODE_WIDTH / 2;
        const y = pos.y + offsetY - NODE_HEIGHT / 2;

        return (
          <div
            key={node.id}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: NODE_WIDTH,
              height: NODE_HEIGHT,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: 12,
              background: "rgba(255,255,255,0.06)",
              backdropFilter: "blur(8px)",
              border: `1.5px solid ${accentColor}40`,
              boxShadow: `0 0 20px ${accentColor}20, inset 0 1px 0 ${accentColor}20`,
              opacity,
              transform: `scale(${0.8 + 0.2 * s})`,
              transition: "opacity 0.05s linear",
            }}
          >
            <span
              style={{
                color: "#fff",
                fontSize: 14,
                fontWeight: "600",
                textAlign: "center",
                lineHeight: 1.2,
                padding: "0 8px",
              }}
            >
              {node.label}
            </span>
            {node.sublabel && (
              <span
                style={{
                  color: "rgba(255,255,255,0.45)",
                  fontSize: 11,
                  textAlign: "center",
                  marginTop: 2,
                  padding: "0 8px",
                }}
              >
                {node.sublabel}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};
