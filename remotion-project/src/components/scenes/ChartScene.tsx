import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { colors, fonts } from "../../design-tokens";

export const ChartSceneSchema = z.object({
  chartType: z.enum(["bar", "line"]).default("bar"),
  title: z.string().optional(),
  data: z.array(z.object({ label: z.string(), value: z.number() })),
  yAxisLabel: z.string().optional(),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type ChartSceneProps = z.infer<typeof ChartSceneSchema>;

const PAD = { top: 80, right: 60, bottom: 90, left: 100 };
const W = 1920;
const H = 1080;
const PLOT_W = W - PAD.left - PAD.right;
const PLOT_H = H - PAD.top - PAD.bottom;

export const ChartScene: React.FC<ChartSceneProps> = ({
  chartType,
  title,
  data,
  yAxisLabel,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  const maxVal = Math.max(...data.map((d) => d.value), 1);
  const niceMax = Math.ceil(maxVal * 1.1);
  const tickCount = 5;
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) => (niceMax / tickCount) * i);

  const totalRevealFrames = 60;
  const perItem = Math.max(6, Math.floor(totalRevealFrames / Math.max(data.length, 1)));

  const xForBar = (i: number) => PAD.left + (i + 0.5) * (PLOT_W / data.length);
  const barW = (PLOT_W / data.length) * 0.6;
  const yForVal = (v: number) => PAD.top + PLOT_H - (v / niceMax) * PLOT_H;

  const xForLinePoint = (i: number) =>
    PAD.left + (data.length === 1 ? PLOT_W / 2 : (i / (data.length - 1)) * PLOT_W);
  const linePoints = data.map((d, i) => ({ x: xForLinePoint(i), y: yForVal(d.value) }));
  const visibleLinePoints = Math.ceil(
    interpolate(frame, [10, 10 + totalRevealFrames], [1, data.length], {
      extrapolateLeft: "clamp", extrapolateRight: "clamp",
    }),
  );
  const linePath = linePoints
    .slice(0, visibleLinePoints)
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  return (
    <AbsoluteFill style={{ background: colors.backgroundGradient, opacity }}>
      {title && (
        <div style={{
          position: "absolute", top: 28, left: 0, right: 0, textAlign: "center",
          fontSize: 32, fontWeight: "700", color: colors.text,
          opacity: titleOpacity, letterSpacing: "-0.3px",
        }}>
          {title}
        </div>
      )}
      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {ticks.map((t, i) => {
          const y = yForVal(t);
          return (
            <g key={i}>
              <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="rgba(255,255,255,0.08)" strokeWidth={1} />
              <text x={PAD.left - 16} y={y + 5} fill={colors.textMuted} fontSize={20} textAnchor="end" fontFamily={fonts.sans}>
                {Math.round(t)}
              </text>
            </g>
          );
        })}
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + PLOT_H} stroke="rgba(255,255,255,0.3)" strokeWidth={2} />
        <line x1={PAD.left} y1={PAD.top + PLOT_H} x2={W - PAD.right} y2={PAD.top + PLOT_H} stroke="rgba(255,255,255,0.3)" strokeWidth={2} />

        {chartType === "bar" && data.map((d, i) => {
          const x = xForBar(i);
          const itemFrame = frame - i * perItem;
          const grow = interpolate(itemFrame, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          const barH = (d.value / niceMax) * PLOT_H * grow;
          return (
            <g key={i}>
              <rect x={x - barW / 2} y={PAD.top + PLOT_H - barH} width={barW} height={barH} fill={colors.primary} rx={4} opacity={0.9} />
              <text x={x} y={PAD.top + PLOT_H + 36} fill={colors.text} fontSize={20} textAnchor="middle" fontFamily={fonts.sans}>
                {d.label}
              </text>
            </g>
          );
        })}

        {chartType === "line" && (
          <>
            {linePoints.slice(0, visibleLinePoints).map((p, i) => (
              <circle key={i} cx={p.x} cy={p.y} r={6} fill={colors.primary} opacity={0.95} />
            ))}
            {visibleLinePoints > 1 && (
              <path d={linePath} fill="none" stroke={colors.primary} strokeWidth={3} opacity={0.9} />
            )}
            {data.map((d, i) => (
              <text key={i} x={xForLinePoint(i)} y={PAD.top + PLOT_H + 36} fill={colors.text} fontSize={20} textAnchor="middle" fontFamily={fonts.sans}>
                {d.label}
              </text>
            ))}
          </>
        )}
      </svg>
      {yAxisLabel && (
        <div style={{
          position: "absolute", left: 24, top: PAD.top, height: PLOT_H,
          display: "flex", alignItems: "center",
          transform: "rotate(-90deg)", transformOrigin: "left center",
          fontSize: 18, color: colors.textMuted, letterSpacing: 1,
        }}>
          {yAxisLabel}
        </div>
      )}
    </AbsoluteFill>
  );
};
