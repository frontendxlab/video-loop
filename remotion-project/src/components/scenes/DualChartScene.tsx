import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { colors, fonts } from "../../design-tokens";

export const DualChartSceneSchema = z.object({
  type: z.literal("dualChart"),
  title: z.string().optional(),
  barData: z.array(z.object({ label: z.string(), value: z.number() })),
  lineData: z.array(z.object({ label: z.string(), value: z.number() })),
  barLabel: z.string().optional().default("Bars"),
  lineLabel: z.string().optional().default("Line"),
  leftAxisLabel: z.string().optional(),
  rightAxisLabel: z.string().optional(),
  duration: z.number().positive(),
  wordTimestamps: z
    .array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() }))
    .optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type DualChartSceneProps = z.infer<typeof DualChartSceneSchema>;

const PAD = { top: 90, right: 100, bottom: 90, left: 100 };
const LEGEND_W = 220;
const LEGEND_H = 52;
const W = 1920;
const H = 1080;
const PLOT_W = W - PAD.left - PAD.right;
const PLOT_H = H - PAD.top - PAD.bottom;

export const DualChartScene: React.FC<DualChartSceneProps> = ({
  title,
  barData,
  lineData,
  barLabel,
  lineLabel,
  leftAxisLabel,
  rightAxisLabel,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  const barMax = Math.max(...barData.map((d) => d.value), 1);
  const lineMax = Math.max(...lineData.map((d) => d.value), 1);
  const niceBarMax = Math.ceil(barMax * 1.15);
  const niceLineMax = Math.ceil(lineMax * 1.15);
  const tickCount = 5;
  const barTicks = Array.from({ length: tickCount + 1 }, (_, i) =>
    Math.round((niceBarMax / tickCount) * i),
  );
  const lineTicks = Array.from({ length: tickCount + 1 }, (_, i) =>
    Math.round((niceLineMax / tickCount) * i),
  );

  const totalRevealFrames = 60;
  const barCount = Math.max(barData.length, 1);
  const perBar = Math.max(4, Math.floor(totalRevealFrames / barCount));

  const barW = (PLOT_W / barCount) * 0.55;
  const xForBar = (i: number) =>
    PAD.left + (i + 0.5) * (PLOT_W / barCount);
  const yForBarVal = (v: number) =>
    PAD.top + PLOT_H - (v / niceBarMax) * PLOT_H;

  const xForLinePoint = (i: number) => {
    const count = lineData.length;
    return count <= 1
      ? PAD.left + PLOT_W / 2
      : PAD.left + (i / (count - 1)) * PLOT_W;
  };
  const yForLineVal = (v: number) =>
    PAD.top + PLOT_H - (v / niceLineMax) * PLOT_H;

  const linePoints = lineData.map((d, i) => ({
    x: xForLinePoint(i),
    y: yForLineVal(d.value),
  }));

  const visibleLinePoints = Math.ceil(
    interpolate(frame, [10, 10 + totalRevealFrames], [1, lineData.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  const linePath = linePoints
    .slice(0, visibleLinePoints)
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  const barColor = colors.primary;
  const lineColor = colors.accent;

  const legendX = W - PAD.right - LEGEND_W;
  const legendY = PAD.top - 56;

  return (
    <AbsoluteFill style={{ background: colors.backgroundGradient, opacity }}>
      {title && (
        <div
          style={{
            position: "absolute",
            top: 28,
            left: 0,
            right: 0,
            textAlign: "center",
            fontSize: 32,
            fontWeight: "700",
            color: colors.text,
            opacity: titleOpacity,
            letterSpacing: "-0.3px",
          }}
        >
          {title}
        </div>
      )}

      {/* Legend */}
      <div
        style={{
          position: "absolute",
          left: legendX,
          top: legendY,
          width: LEGEND_W,
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          gap: 24,
          background: colors.surface,
          borderRadius: 8,
          border: `1px solid ${colors.chromeBorder}`,
          padding: "0 16px",
          opacity: title ? 1 : opacity,
        }}
      >
        <LegendItem color={barColor} label={barLabel} />
        <LegendItem color={lineColor} label={lineLabel} />
      </div>

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        {/* Left axis grid lines & tick labels */}
        {barTicks.map((t, i) => {
          const y = yForBarVal(t);
          return (
            <g key={`bar-tick-${i}`}>
              <line
                x1={PAD.left}
                y1={y}
                x2={W - PAD.right}
                y2={y}
                stroke="rgba(255,255,255,0.06)"
                strokeWidth={1}
              />
              <text
                x={PAD.left - 12}
                y={y + 5}
                fill={colors.textMuted}
                fontSize={18}
                textAnchor="end"
                fontFamily={fonts.sans}
              >
                {t}
              </text>
            </g>
          );
        })}

        {/* Right axis tick labels */}
        {lineTicks.map((t, i) => {
          const y = yForLineVal(t);
          return (
            <text
              key={`line-tick-${i}`}
              x={W - PAD.right + 12}
              y={y + 5}
              fill={colors.textMuted}
              fontSize={18}
              textAnchor="start"
              fontFamily={fonts.sans}
            >
              {t}
            </text>
          );
        })}

        {/* Axes */}
        <line
          x1={PAD.left}
          y1={PAD.top}
          x2={PAD.left}
          y2={PAD.top + PLOT_H}
          stroke="rgba(255,255,255,0.25)"
          strokeWidth={2}
        />
        <line
          x1={PAD.left}
          y1={PAD.top + PLOT_H}
          x2={W - PAD.right}
          y2={PAD.top + PLOT_H}
          stroke="rgba(255,255,255,0.25)"
          strokeWidth={2}
        />
        <line
          x1={W - PAD.right}
          y1={PAD.top}
          x2={W - PAD.right}
          y2={PAD.top + PLOT_H}
          stroke="rgba(255,255,255,0.25)"
          strokeWidth={2}
        />

        {/* Bars */}
        {barData.map((d, i) => {
          const x = xForBar(i);
          const itemFrame = frame - i * perBar;
          const grow = interpolate(itemFrame, [0, 20], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          });
          const barH = (d.value / niceBarMax) * PLOT_H * grow;
          return (
            <g key={`bar-${i}`}>
              <rect
                x={x - barW / 2}
                y={PAD.top + PLOT_H - barH}
                width={barW}
                height={barH}
                fill={barColor}
                rx={4}
                opacity={0.85}
              />
              <text
                x={x}
                y={PAD.top + PLOT_H + 36}
                fill={colors.text}
                fontSize={18}
                textAnchor="middle"
                fontFamily={fonts.sans}
              >
                {d.label}
              </text>
            </g>
          );
        })}

        {/* Line */}
        {linePoints.slice(0, visibleLinePoints).map((p, i) => (
          <circle
            key={`dot-${i}`}
            cx={p.x}
            cy={p.y}
            r={5}
            fill={lineColor}
            opacity={0.95}
          />
        ))}
        {visibleLinePoints > 1 && (
          <path
            d={linePath}
            fill="none"
            stroke={lineColor}
            strokeWidth={3}
            opacity={0.85}
          />
        )}

        {/* X-axis labels for line (only if lineData has different labels) */}
        {lineData.length > 0 &&
          barData.length !== lineData.length &&
          lineData.map((d, i) => (
            <text
              key={`xlabel-${i}`}
              x={xForLinePoint(i)}
              y={PAD.top + PLOT_H + 56}
              fill={colors.textSubtle}
              fontSize={14}
              textAnchor="middle"
              fontFamily={fonts.sans}
            >
              {d.label}
            </text>
          ))}
      </svg>

      {/* Left axis label */}
      {leftAxisLabel && (
        <div
          style={{
            position: "absolute",
            left: 24,
            top: PAD.top,
            height: PLOT_H,
            display: "flex",
            alignItems: "center",
            transform: "rotate(-90deg)",
            transformOrigin: "left center",
            fontSize: 16,
            color: colors.textMuted,
            letterSpacing: 1,
            whiteSpace: "nowrap",
          }}
        >
          {leftAxisLabel}
        </div>
      )}

      {/* Right axis label */}
      {rightAxisLabel && (
        <div
          style={{
            position: "absolute",
            right: 24,
            top: PAD.top,
            height: PLOT_H,
            display: "flex",
            alignItems: "center",
            transform: "rotate(90deg)",
            transformOrigin: "right center",
            fontSize: 16,
            color: colors.textMuted,
            letterSpacing: 1,
            whiteSpace: "nowrap",
          }}
        >
          {rightAxisLabel}
        </div>
      )}
    </AbsoluteFill>
  );
};

const LegendItem: React.FC<{ color: string; label: string }> = ({
  color,
  label,
}) => (
  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
    <svg width={14} height={14}>
      <rect x={0} y={2} width={14} height={10} rx={2} fill={color} />
    </svg>
    <span
      style={{
        fontSize: 16,
        color: colors.text,
        fontFamily: fonts.sans,
        fontWeight: 500,
      }}
    >
      {label}
    </span>
  </div>
);
