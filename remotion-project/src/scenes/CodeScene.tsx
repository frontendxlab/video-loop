import React from "react";
import { useCurrentFrame } from "remotion";
import { z } from "zod";

export const CodeSceneSchema = z.object({
  code: z.string(),
  lang: z.enum(["javascript", "python", "typescript", "rust", "go"]),
  highlightLines: z.array(z.number()).optional(),
  caption: z.string().optional(),
  duration: z.number().positive(),
});

export type CodeSceneProps = z.infer<typeof CodeSceneSchema>;

const LINE_HEIGHT = 28;
const PADDING = 20;

export const CodeScene: React.FC<CodeSceneProps> = ({
  code,
  lang,
  highlightLines,
  caption,
}) => {
  const frame = useCurrentFrame();
  const lines = code.split("\n");
  const totalLines = lines.length;
  const revealProgress = Math.min(1, frame / 15);

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#0d1117",
        padding: PADDING,
        width: "100%",
        height: "100%",
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontSize: 16,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "8px 0",
          marginBottom: 8,
          borderBottom: "1px solid #30363d",
        }}
      >
        <span
          style={{
            color: "#8b949e",
            fontSize: 12,
            textTransform: "uppercase",
            letterSpacing: 1,
          }}
        >
          {lang}
        </span>
        {caption && (
          <span style={{ color: "#8b949e", fontSize: 12, marginLeft: 12 }}>
            {caption}
          </span>
        )}
      </div>
      <div style={{ flex: 1, overflow: "hidden" }}>
        {lines.map((line, i) => {
          const isHighlighted = highlightLines?.includes(i + 1);
          const lineOpacity = Math.min(
            1,
            (frame - i * 2) / 10,
          );

          return (
            <div
              key={i}
              style={{
                display: "flex",
                height: LINE_HEIGHT,
                alignItems: "center",
                backgroundColor: isHighlighted
                  ? "rgba(255, 235, 59, 0.1)"
                  : "transparent",
                borderLeft: isHighlighted
                  ? "3px solid #ffeb3b"
                  : "3px solid transparent",
                opacity: Math.min(revealProgress, lineOpacity),
                transition: "opacity 0.3s",
              }}
            >
              <span
                style={{
                  width: 40,
                  minWidth: 40,
                  textAlign: "right",
                  paddingRight: 16,
                  color: "#484f58",
                  userSelect: "none",
                }}
              >
                {i + 1}
              </span>
              <span
                style={{
                  color: isHighlighted ? "#ffeb3b" : "#c9d1d9",
                  whiteSpace: "pre",
                }}
              >
                {line || " "}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
