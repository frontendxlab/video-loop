import React from "react";
import { useCurrentFrame } from "remotion";
import { z } from "zod";

export const BulletSceneSchema = z.object({
  points: z.array(z.string()).min(2).max(5),
  entry: z.enum(["fadeIn", "slideIn", "scaleIn"]).optional().default("fadeIn"),
  duration: z.number().positive(),
});

export type BulletSceneProps = z.infer<typeof BulletSceneSchema>;

const STAGGER_FRAMES = 30;
const ENTRY_DURATION = 20;

function getEntryStyle(
  frame: number,
  entry: "fadeIn" | "slideIn" | "scaleIn",
): React.CSSProperties {
  const progress = Math.min(1, frame / ENTRY_DURATION);

  switch (entry) {
    case "fadeIn":
      return { opacity: progress };
    case "slideIn":
      return {
        opacity: progress,
        transform: `translateX(${40 * (1 - progress)}px)`,
      };
    case "scaleIn":
      return {
        opacity: progress,
        transform: `scale(${0.5 + 0.5 * progress})`,
      };
  }
}

export const BulletScene: React.FC<BulletSceneProps> = ({
  points,
  entry = "fadeIn",
}) => {
  const frame = useCurrentFrame();
  const activeIndex = Math.min(
    Math.floor(frame / STAGGER_FRAMES),
    points.length - 1,
  );

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: 60,
        backgroundColor: "#1a1a2e",
        width: "100%",
        height: "100%",
      }}
    >
      {points.map((point, i) => {
        const itemFrame = frame - i * STAGGER_FRAMES;
        const isActive = i === activeIndex;
        const isDimmed = i < activeIndex;

        const entryStyle = itemFrame >= 0
          ? getEntryStyle(itemFrame, entry)
          : { opacity: 0, transform: "scale(0.5)" };

        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              marginBottom: 20,
              opacity: isDimmed ? 0.5 : entryStyle.opacity ?? 1,
              transform: entryStyle.transform,
              transition: "opacity 0.3s, transform 0.3s",
            }}
          >
            <span
              style={{
                width: 32,
                height: 32,
                borderRadius: 16,
                backgroundColor: isActive ? "#ffeb3b" : isDimmed ? "#555" : "#ffeb3b",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginRight: 16,
                color: isActive ? "#1a1a2e" : "#fff",
                fontWeight: "bold",
                fontSize: 14,
                flexShrink: 0,
              }}
            >
              {i + 1}
            </span>
            <span
              style={{
                fontSize: 24,
                color: isActive ? "#fff" : isDimmed ? "#888" : "#ccc",
              }}
            >
              {point}
            </span>
          </div>
        );
      })}
    </div>
  );
};
