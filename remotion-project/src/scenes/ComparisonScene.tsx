import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { z } from "zod";

export const ComparisonSceneSchema = z.object({
  labelBefore: z.string(),
  labelAfter: z.string(),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type ComparisonSceneProps = z.infer<typeof ComparisonSceneSchema>;

export const ComparisonScene: React.FC<ComparisonSceneProps> = ({
  labelBefore,
  labelAfter,
}) => {
  const frame = useCurrentFrame();
  const sweepProgress = Math.min(1, frame / 30);

  const leftClip = `${sweepProgress * 50}%`;
  const dividerLeft = `${sweepProgress * 50}%`;

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        backgroundColor: "#1a1a2e",
        width: "100%",
        height: "100%",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: leftClip,
          backgroundColor: "#16213e",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "0 20px",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 14,
              color: "#8b949e",
              textTransform: "uppercase",
              letterSpacing: 2,
              marginBottom: 8,
            }}
          >
            Before
          </div>
          <div
            style={{
              fontSize: 28,
              color: "#fff",
              fontWeight: "bold",
            }}
          >
            {labelBefore}
          </div>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: dividerLeft,
          top: 0,
          bottom: 0,
          width: 3,
          backgroundColor: "#ffeb3b",
          zIndex: 10,
          boxShadow: "0 0 8px rgba(255, 235, 59, 0.5)",
        }}
      />

      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          bottom: 0,
          width: `${100 - sweepProgress * 50}%`,
          backgroundColor: "#0f3460",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            padding: "0 20px",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 14,
              color: "#8b949e",
              textTransform: "uppercase",
              letterSpacing: 2,
              marginBottom: 8,
            }}
          >
            After
          </div>
          <div
            style={{
              fontSize: 28,
              color: "#fff",
              fontWeight: "bold",
            }}
          >
            {labelAfter}
          </div>
        </div>
      </div>
    </div>
  );
};
