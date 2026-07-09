import React from "react";
import { useCurrentFrame } from "remotion";
import { z } from "zod";

const NodeSchema = z.object({
  id: z.string(),
  label: z.string(),
  position: z.object({
    row: z.number(),
    col: z.number(),
  }),
});

export const DiagramSceneSchema = z.object({
  config: z.object({
    nodes: z.array(NodeSchema),
  }),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type DiagramSceneProps = z.infer<typeof DiagramSceneSchema>;

const NODE_WIDTH = 160;
const NODE_HEIGHT = 60;
const GAP_X = 40;
const GAP_Y = 30;
const PADDING = 40;

export const DiagramScene: React.FC<DiagramSceneProps> = ({
  config,
}) => {
  const frame = useCurrentFrame();

  const maxRow = Math.max(...config.nodes.map((n) => n.position.row), 0);
  const maxCol = Math.max(...config.nodes.map((n) => n.position.col), 0);

  const totalWidth = (maxCol + 1) * (NODE_WIDTH + GAP_X) - GAP_X + PADDING * 2;
  const totalHeight = (maxRow + 1) * (NODE_HEIGHT + GAP_Y) - GAP_Y + PADDING * 2;

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#1a1a2e",
        width: "100%",
        height: "100%",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "relative",
          width: totalWidth,
          height: totalHeight,
        }}
      >
        {config.nodes.map((node, i) => {
          const x = PADDING + node.position.col * (NODE_WIDTH + GAP_X);
          const y = PADDING + node.position.row * (NODE_HEIGHT + GAP_Y);
          const nodeProgress = Math.min(1, (frame - i * 5) / 15);

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
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "rgba(255, 235, 59, 0.15)",
                border: "2px solid #ffeb3b",
                borderRadius: 8,
                opacity: nodeProgress,
                transform: `scale(${nodeProgress})`,
              }}
            >
              <span
                style={{
                  color: "#fff",
                  fontSize: 14,
                  textAlign: "center",
                  padding: "0 8px",
                  wordBreak: "break-word",
                }}
              >
                {node.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
