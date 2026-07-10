/** MapScene — deterministic SVG geo visualization. No tile deps.
 *
 * Renders lat/lng → 2D projection with markers, routes, grid.
 * All deterministic per frame — no API calls, no tiles.
 *
 * ponytail: true Mercator projection, clustering, tooltips. Add when
 * map needs to cover poles or handle >50 markers.
 */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { z } from "zod";
import { colors, fonts } from "../design-tokens";

/* ── Schema ─────────────────────────────────────────────────── */

export const MapSceneSchema = z.object({
  type: z.literal("map-geo"),
  centerLat: z.number(),
  centerLng: z.number(),
  zoom: z.number().int().positive().default(5),
  style: z.enum(["streets", "satellite", "dark"]).default("streets"),
  title: z.string().optional(),
  markers: z
    .array(
      z.object({
        lat: z.number(),
        lng: z.number(),
        label: z.string().optional(),
        color: z.string().optional(),
      }),
    )
    .optional()
    .default([]),
  routes: z
    .array(
      z.object({
        points: z.array(z.object({ lat: z.number(), lng: z.number() })),
        color: z.string().optional(),
        width: z.number().optional(),
      }),
    )
    .optional()
    .default([]),
  duration: z.number().positive(),
  wordTimestamps: z
    .array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() }))
    .optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type MapSceneProps = z.infer<typeof MapSceneSchema>;

/* ── Projection ─────────────────────────────────────────────── */

function project(
  lat: number,
  lng: number,
  cLat: number,
  cLng: number,
  zoom: number,
  w: number,
  h: number,
): { x: number; y: number } {
  const scale = (zoom * w) / 360;
  const x = w / 2 + (lng - cLng) * scale;
  const y = h / 2 - (lat - cLat) * scale; // SVG y inverted
  return { x, y };
}

/* ── Style presets ──────────────────────────────────────────── */

const STYLE_BG: Record<string, string> = {
  streets: "#1a2332",
  satellite: "#0d1b2a",
  dark: "#0f0f1a",
};

const STYLE_GRID: Record<string, string> = {
  streets: "rgba(148,163,184,0.12)",
  satellite: "rgba(148,163,184,0.08)",
  dark: "rgba(255,255,255,0.06)",
};

/* ── Helpers ────────────────────────────────────────────────── */

const PIN_PATH =
  "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z";

/* ── Component ──────────────────────────────────────────────── */

export const MapScene: React.FC<MapSceneProps> = ({
  centerLat,
  centerLng,
  zoom = 5,
  style = "streets",
  title,
  markers = [],
  routes = [],
  wordTimestamps,
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const pad = 80;
  const mapW = width - pad * 2;
  const mapH = height - pad * 2;
  const mapX = pad;
  const mapY = pad + (title ? 60 : 0);

  // Fade in
  const opacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: "clamp" });

  // Route draw progress
  const routeProgress = interpolate(frame, [30, 120], [0, 1], { extrapolateRight: "clamp", extrapolateLeft: "clamp" });

  // Build grid lines
  const gridLines: React.ReactNode[] = [];
  const steps = Math.max(3, zoom * 2);
  const latStep = 360 / steps;
  const lngStep = 360 / steps;
  const gridColor = STYLE_GRID[style] || STYLE_GRID.streets;

  for (let i = -steps; i <= steps; i++) {
    const lat = centerLat + i * latStep;
    const p1 = project(lat, centerLng - 180, centerLat, centerLng, zoom, mapW, mapH);
    if (p1.y >= -1000 && p1.y <= height + 1000) {
      gridLines.push(
        <line
          key={`lat-${i}`}
          x1={mapX}
          y1={mapY + p1.y}
          x2={mapX + mapW}
          y2={mapY + p1.y}
          stroke={gridColor}
          strokeWidth={1}
        />,
      );
    }
    const lng = centerLng + i * lngStep;
    const p2 = project(centerLat, lng, centerLat, centerLng, zoom, mapW, mapH);
    if (p2.x >= -1000 && p2.x <= width + 1000) {
      gridLines.push(
        <line
          key={`lng-${i}`}
          x1={mapX + p2.x}
          y1={mapY}
          x2={mapX + p2.x}
          y2={mapY + mapH}
          stroke={gridColor}
          strokeWidth={1}
        />,
      );
    }
  }

  // Build routes
  const routeElements: React.ReactNode[] = [];
  for (let ri = 0; ri < routes.length; ri++) {
    const r = routes[ri];
    if (!r.points || r.points.length < 2) continue;
    const pts = r.points.map((pt) =>
      project(pt.lat, pt.lng, centerLat, centerLng, zoom, mapW, mapH),
    );
    // Dash offset animation
    const totalLen = pts.reduce((acc, pt, i) => {
      if (i === 0) return acc;
      const dx = pt.x - pts[i - 1].x;
      const dy = pt.y - pts[i - 1].y;
      return acc + Math.sqrt(dx * dx + dy * dy);
    }, 0);

    const pathD = pts.map((pt, i) => (i === 0 ? `M${mapX + pt.x},${mapY + pt.y}` : `L${mapX + pt.x},${mapY + pt.y}`)).join(" ");

    routeElements.push(
      <path
        key={`route-${ri}`}
        d={pathD}
        fill="none"
        stroke={r.color || "#F59E0B"}
        strokeWidth={r.width || 3}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={totalLen}
        strokeDashoffset={totalLen * (1 - routeProgress)}
        opacity={opacity}
      />,
    );
  }

  // Build markers
  const markerElements = markers.map((m, i) => {
    const pt = project(m.lat, m.lng, centerLat, centerLng, zoom, mapW, mapH);
    const color = m.color || "#4A90D9";
    const show = frame > 30 + i * 5;
    const mOpacity = show ? Math.min(1, (frame - (30 + i * 5)) / 10) : 0;
    return (
      <g key={`marker-${i}`} opacity={mOpacity}>
        <path
          d={PIN_PATH}
          fill={color}
          transform={`translate(${mapX + pt.x - 12}, ${mapY + pt.y - 22}) scale(1.2)`}
        />
        {m.label ? (
          <text
            x={mapX + pt.x}
            y={mapY + pt.y + 20}
            fill="#E5EEF8"
            fontFamily={fonts.sans}
            fontSize={14}
            fontWeight="600"
            textAnchor="middle"
          >
            {m.label}
          </text>
        ) : null}
      </g>
    );
  });

  // Title overlay
  const titleOpacity = wordTimestamps && wordTimestamps.length > 0
    ? (frame >= sceneStartFrame + 30 ? Math.min(1, (frame - sceneStartFrame - 30) / 15) : 0)
    : Math.min(1, frame / 40);

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, ${STYLE_BG[style] || STYLE_BG.streets} 0%, #162033 100%)`,
      }}
    >
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {gridLines}
        {routeElements}
        {markerElements}
      </svg>

      {/* Border frame */}
      <div
        style={{
          position: "absolute",
          left: mapX - 1,
          top: mapY - 1,
          width: mapW + 2,
          height: mapH + 2,
          border: "1px solid rgba(148,163,184,0.15)",
          borderRadius: 12,
          pointerEvents: "none",
        }}
      />

      {title ? (
        <div
          style={{
            position: "absolute",
            top: pad - 10,
            left: 0,
            width: "100%",
            textAlign: "center",
            opacity: titleOpacity,
          }}
        >
          <span
            style={{
              fontFamily: fonts.heading,
              fontSize: 28,
              fontWeight: 700,
              color: colors.text,
              letterSpacing: "-0.3px",
            }}
          >
            {title}
          </span>
        </div>
      ) : null}

      {/* Zoom badge */}
      <div
        style={{
          position: "absolute",
          bottom: pad - 10,
          right: pad,
          fontFamily: fonts.mono,
          fontSize: 12,
          color: "rgba(229,238,248,0.4)",
        }}
      >
        zoom {zoom}
      </div>
    </AbsoluteFill>
  );
};
