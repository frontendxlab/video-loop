import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { colors, fonts } from "../design-tokens";

export const ScreenflowSceneSchema = z.object({
  device: z.enum(["phone", "browser"]).default("browser"),
  screenshot: z.string(),
  title: z.string().optional(),
  callouts: z.array(z.object({
    text: z.string().min(1),
    x: z.number().min(0).max(100),
    y: z.number().min(0).max(100),
  })).optional().default([]),
  cursorPath: z.array(z.object({
    x: z.number().min(0).max(100),
    y: z.number().min(0).max(100),
    frame: z.number().min(0),
  })).optional().default([]),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type ScreenflowSceneProps = z.infer<typeof ScreenflowSceneSchema>;

const W = 1920;
const H = 1080;
const DEVICE_W = 960;
const DEVICE_H = 600;
const CHROME_H = 44;
const SCREEN_PAD = 12;
const CALLOUT_W = 280;
const DEVICE_LEFT = 80;
const CALLOUT_STAGGER = 25;
const CALLOUT_FADE_DURATION = 20;

const anchorOffsets: Record<string, { x: number; y: number }> = {
  tl: { x: 0, y: 0 },
  t: { x: 50, y: 0 },
  tr: { x: 100, y: 0 },
  r: { x: 100, y: 50 },
  br: { x: 100, y: 100 },
  b: { x: 50, y: 100 },
  bl: { x: 0, y: 100 },
  l: { x: 0, y: 50 },
};

export const ScreenflowScene: React.FC<ScreenflowSceneProps> = ({
  device,
  screenshot,
  title,
  callouts = [],
  cursorPath = [],
  sceneStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = frame - sceneStartFrame;

  const opacity = interpolate(localFrame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const titleOpacity = interpolate(localFrame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const deviceSpring = spring({
    frame: localFrame,
    fps,
    config: { damping: 12, stiffness: 90 },
  });
  const deviceScale = interpolate(deviceSpring, [0, 1], [0.92, 1]);

  const DEVICE_TOP = title ? 200 : 90;
  const SCREEN_X = DEVICE_LEFT + SCREEN_PAD;
  const SCREEN_Y = DEVICE_TOP + CHROME_H + SCREEN_PAD;
  const SCREEN_W = DEVICE_W - SCREEN_PAD * 2;
  const SCREEN_H = DEVICE_H - CHROME_H - SCREEN_PAD * 2;
  const CALLOUT_LEFT = DEVICE_LEFT + DEVICE_W + 40;

  /* Cursor position */
  let cursorVis = 0;
  let cursorAbsX = SCREEN_X;
  let cursorAbsY = SCREEN_Y;

  if (cursorPath.length > 0) {
    const lastIdx = cursorPath.length - 1;
    let segIdx = 0;
    for (let i = lastIdx; i >= 0; i--) {
      if (localFrame >= cursorPath[i].frame) {
        segIdx = i;
        break;
      }
    }
    const cur = cursorPath[segIdx];
    const next = segIdx < lastIdx ? cursorPath[segIdx + 1] : cur;
    const segLen = next.frame - cur.frame || 1;
    const t = Math.min(1, Math.max(0, (localFrame - cur.frame) / segLen));
    const pctX = cur.x + (next.x - cur.x) * t;
    const pctY = cur.y + (next.y - cur.y) * t;
    cursorAbsX = SCREEN_X + (pctX / 100) * SCREEN_W;
    cursorAbsY = SCREEN_Y + (pctY / 100) * SCREEN_H;
    const firstFrame = cursorPath[0].frame;
    if (localFrame >= firstFrame) {
      cursorVis = interpolate(
        Math.max(0, localFrame - firstFrame),
        [0, 5],
        [0, 1],
        { extrapolateRight: "clamp" },
      );
    }
  }

  return (
    <AbsoluteFill
      style={{
        background: colors.backgroundGradient,
        opacity,
        fontFamily: fonts.sans,
      }}
    >
      {title && (
        <div
          style={{
            position: "absolute",
            top: 48,
            left: 0,
            right: 0,
            textAlign: "center",
            fontSize: 34,
            fontWeight: 700,
            color: colors.text,
            fontFamily: fonts.heading,
            opacity: titleOpacity,
            letterSpacing: "-0.3px",
          }}
        >
          {title}
        </div>
      )}

      {/* Device frame */}
      <div
        style={{
          position: "absolute",
          left: DEVICE_LEFT,
          top: DEVICE_TOP,
          width: DEVICE_W,
          height: DEVICE_H,
          borderRadius: device === "phone" ? 36 : 12,
          border: `1px solid ${colors.chromeBorder}`,
          background: colors.chromePanel,
          boxShadow: `0 8px 40px rgba(0,0,0,0.25)`,
          transform: `scale(${deviceScale})`,
          transformOrigin: "top left",
          overflow: "hidden",
        }}
      >
        {/* Browser chrome / phone top */}
        <div
          style={{
            height: CHROME_H,
            display: "flex",
            alignItems: "center",
            padding: "0 16px",
            borderBottom: `1px solid ${colors.chromeBorder}`,
            background: colors.surface,
          }}
        >
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: colors.chromeDotRed,
              }}
            />
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: colors.chromeDotYellow,
              }}
            />
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: colors.chromeDotGreen,
              }}
            />
          </div>
          {device === "browser" && (
            <div
              style={{
                flex: 1,
                marginLeft: 20,
                height: 26,
                borderRadius: 6,
                background: colors.background,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 12,
                color: colors.textMuted,
              }}
            >
              {screenshot.length > 50
                ? screenshot.slice(0, 50) + "\u2026"
                : screenshot}
            </div>
          )}
        </div>

        {/* Screenshot */}
        <img
          src={screenshot}
          alt=""
          style={{
            position: "absolute",
            top: CHROME_H,
            left: 0,
            width: DEVICE_W,
            height: DEVICE_H - CHROME_H,
            objectFit: "cover",
          }}
        />

        {/* Phone notch */}
        {device === "phone" && (
          <div
            style={{
              position: "absolute",
              top: 0,
              left: "50%",
              transform: "translateX(-50%)",
              width: 150,
              height: 28,
              background: colors.black,
              borderBottomLeftRadius: 16,
              borderBottomRightRadius: 16,
              zIndex: 2,
            }}
          />
        )}
      </div>

      {/* Connecting lines (SVG overlay) */}
      {callouts.length > 0 && (
        <svg
          width={W}
          height={H}
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            zIndex: 1,
          }}
        >
          {callouts.map((c, i) => {
            const revealFrame = 15 + i * CALLOUT_STAGGER;
            const lineOpacity = interpolate(
              localFrame - revealFrame,
              [0, CALLOUT_FADE_DURATION],
              [0, 0.45],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            const px = SCREEN_X + (c.x / 100) * SCREEN_W;
            const py = SCREEN_Y + (c.y / 100) * SCREEN_H;
            return (
              <line
                key={i}
                x1={px}
                y1={py}
                x2={CALLOUT_LEFT}
                y2={py}
                stroke={colors.primary}
                strokeWidth={1.5}
                strokeDasharray="4 4"
                opacity={lineOpacity}
              />
            );
          })}
        </svg>
      )}

      {/* Callout cards */}
      {callouts.map((c, i) => {
        const revealFrame = 15 + i * CALLOUT_STAGGER;
        const calloutOpacity = interpolate(
          localFrame - revealFrame,
          [0, CALLOUT_FADE_DURATION],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );
        const calloutSlide = interpolate(
          localFrame - revealFrame,
          [0, CALLOUT_FADE_DURATION],
          [14, 0],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          },
        );
        const py = SCREEN_Y + (c.y / 100) * SCREEN_H;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: CALLOUT_LEFT + 4,
              top: py - 22,
              opacity: calloutOpacity,
              transform: `translateX(${calloutSlide}px)`,
              maxWidth: CALLOUT_W,
              zIndex: 2,
            }}
          >
            <div
              style={{
                padding: "14px 18px",
                background: colors.chromePanel,
                backdropFilter: "blur(12px)",
                borderRadius: 12,
                border: `1px solid ${colors.chromeBorder}`,
                boxShadow: `0 4px 20px rgba(0,0,0,0.15)`,
                fontSize: 15,
                color: colors.text,
                lineHeight: 1.5,
                position: "relative",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  left: -5,
                  top: 16,
                  width: 8,
                  height: 8,
                  background: colors.chromePanel,
                  borderLeft: `1px solid ${colors.chromeBorder}`,
                  borderBottom: `1px solid ${colors.chromeBorder}`,
                  transform: "rotate(45deg)",
                }}
              />
              {c.text}
            </div>
          </div>
        );
      })}

      {/* Cursor */}
      {cursorPath.length > 0 && (
        <div
          style={{
            position: "absolute",
            left: cursorAbsX - 6,
            top: cursorAbsY - 4,
            opacity: cursorVis,
            pointerEvents: "none",
            zIndex: 10,
          }}
        >
          <svg
            width={18}
            height={24}
            viewBox="0 0 18 24"
            fill="none"
            style={{ filter: "drop-shadow(0 1px 3px rgba(0,0,0,0.4))" }}
          >
            <path
              d="M2 3 L2 20 L7 14 L12 22 L15 20 L10 12 L17 12 Z"
              fill={colors.white}
              stroke={colors.text}
              strokeWidth={1.5}
              strokeLinejoin="round"
            />
          </svg>
        </div>
      )}
    </AbsoluteFill>
  );
};
