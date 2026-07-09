import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { z } from "zod";

export const ImageSceneSchema = z.object({
  src: z.string(),
  caption: z.string().optional(),
  effect: z.enum(["kenBurns", "fadeIn", "zoomIn"]).optional().default("fadeIn"),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type ImageSceneProps = z.infer<typeof ImageSceneSchema>;

const EFFECT_DURATION = 30;

export const ImageScene: React.FC<ImageSceneProps> = ({
  src,
  caption,
  effect = "fadeIn",
}) => {
  const frame = useCurrentFrame();

  const opacity = effect === "fadeIn"
    ? Math.min(1, frame / EFFECT_DURATION)
    : 1;

  const scale = effect === "kenBurns"
    ? interpolate(frame, [0, 90], [1.0, 1.15])
    : effect === "zoomIn"
      ? interpolate(frame, [0, EFFECT_DURATION], [0.8, 1.0])
      : 1;

  const translateX = effect === "kenBurns"
    ? interpolate(frame, [0, 90], [0, -20])
    : 0;

  const translateY = effect === "kenBurns"
    ? interpolate(frame, [0, 90], [0, -10])
    : 0;

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#0d1117",
        width: "100%",
        height: "100%",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: "100%",
          height: caption ? "85%" : "100%",
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <img
          src={src}
          style={{
            maxWidth: "100%",
            maxHeight: "100%",
            objectFit: "contain",
            opacity,
            transform: `scale(${scale}) translateX(${translateX}px) translateY(${translateY}px)`,
          }}
        />
      </div>
      {caption && (
        <div
          style={{
            height: "15%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 40px",
          }}
        >
          <span
            style={{
              color: "#c9d1d9",
              fontSize: 20,
              textAlign: "center",
              opacity: Math.min(1, (frame - 10) / 20),
            }}
          >
            {caption}
          </span>
        </div>
      )}
    </div>
  );
};
