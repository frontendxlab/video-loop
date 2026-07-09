import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";
import { z } from "zod";

export const TimelineSceneSchema = z.object({
  title: z.string().optional(),
  events: z.array(z.object({
    label: z.string(),
    date: z.string().optional(),
  })).min(1),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type TimelineSceneProps = z.infer<typeof TimelineSceneSchema>;

const PAD = { top: 130, bottom: 130, left: 140, right: 140 };
const W = 1920;
const H = 1080;
const AXIS_Y = H / 2;
const AXIS_W = W - PAD.left - PAD.right;

export const TimelineScene: React.FC<TimelineSceneProps> = ({ title, events }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  const progress = interpolate(frame, [10, 90], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const filledW = AXIS_W * progress;

  const xFor = (i: number) =>
    PAD.left + (events.length === 1 ? AXIS_W / 2 : (i / (events.length - 1)) * AXIS_W);

  return (
    <AbsoluteFill style={{ background: "linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%)", opacity }}>
      {title && (
        <div style={{
          position: "absolute", top: 40, left: 0, right: 0, textAlign: "center",
          fontSize: 32, fontWeight: "700", color: "rgba(255,255,255,0.95)",
          opacity: titleOpacity, letterSpacing: "-0.3px",
        }}>
          {title}
        </div>
      )}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <line x1={PAD.left} y1={AXIS_Y} x2={PAD.left + AXIS_W} y2={AXIS_Y} stroke="rgba(255,255,255,0.15)" strokeWidth={4} />
        <line x1={PAD.left} y1={AXIS_Y} x2={PAD.left + filledW} y2={AXIS_Y} stroke="#4a90d9" strokeWidth={4} strokeLinecap="round" />
        {events.map((e, i) => {
          const x = xFor(i);
          const reached = x <= PAD.left + filledW + 1;
          const nodeScale = reached
            ? interpolate(frame, [10 + i * 15, 10 + i * 15 + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) })
            : 0;
          const labelOpacity = reached ? Math.min(1, nodeScale * 1.2) : 0;
          const above = i % 2 === 0;
          const labelY = above ? AXIS_Y - 70 : AXIS_Y + 70;
          return (
            <g key={i} opacity={labelOpacity}>
              <circle cx={x} cy={AXIS_Y} r={10 * nodeScale} fill={reached ? "#7c5cbf" : "rgba(255,255,255,0.3)"} />
              <line x1={x} y1={AXIS_Y} x2={x} y2={labelY} stroke="rgba(255,255,255,0.3)" strokeWidth={1.5} />
              <text x={x} y={labelY + (above ? -10 : 22)} fill="rgba(255,255,255,0.95)" fontSize={22} textAnchor="middle" fontWeight="600" fontFamily="Inter, sans-serif">
                {e.label}
              </text>
              {e.date && (
                <text x={x} y={labelY + (above ? -36 : 48)} fill="rgba(255,255,255,0.5)" fontSize={16} textAnchor="middle" fontFamily="Inter, sans-serif">
                  {e.date}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
