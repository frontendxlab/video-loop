import React from "react";
import { useCurrentFrame } from "remotion";
import { z } from "zod";

export const DiffSceneSchema = z.object({
  oldCode: z.string(),
  newCode: z.string(),
  lang: z.string(),
  duration: z.number().positive(),
  wordTimestamps: z.array(z.object({ text: z.string(), startMs: z.number(), endMs: z.number() })).optional(),
  sceneStartFrame: z.number().optional().default(0),
});

export type DiffSceneProps = z.infer<typeof DiffSceneSchema>;

const LINE_HEIGHT = 28;

function diffLines(
  oldLines: string[],
  newLines: string[],
): { line: string; type: "added" | "removed" | "unchanged" }[] {
  const maxLen = Math.max(oldLines.length, newLines.length);
  const result: { line: string; type: "added" | "removed" | "unchanged" }[] = [];

  for (let i = 0; i < maxLen; i++) {
    if (i >= oldLines.length) {
      result.push({ line: newLines[i], type: "added" });
    } else if (i >= newLines.length) {
      result.push({ line: oldLines[i], type: "removed" });
    } else if (oldLines[i] !== newLines[i]) {
      result.push({ line: oldLines[i], type: "removed" });
      result.push({ line: newLines[i], type: "added" });
    } else {
      result.push({ line: oldLines[i], type: "unchanged" });
    }
  }
  return result;
}

export const DiffScene: React.FC<DiffSceneProps> = ({
  oldCode,
  newCode,
  lang,
}) => {
  const frame = useCurrentFrame();
  const oldLines = oldCode.split("\n");
  const newLines = newCode.split("\n");
  const diffOld = diffLines(oldLines, newLines).filter(
    (l) => l.type !== "added",
  );
  const diffNew = diffLines(oldLines, newLines).filter(
    (l) => l.type !== "removed",
  );

  const revealProgress = Math.min(1, frame / 20);

  const renderColumn = (
    lines: { line: string; type: "added" | "removed" | "unchanged" }[],
    side: "left" | "right",
  ) => (
    <div
      style={{
        flex: 1,
        overflow: "hidden",
        borderRight: side === "left" ? "1px solid #30363d" : "none",
        paddingRight: side === "left" ? 8 : 0,
        paddingLeft: side === "right" ? 8 : 0,
      }}
    >
      <div
        style={{
          padding: "8px 12px",
          borderBottom: "1px solid #30363d",
          color: "#8b949e",
          fontSize: 12,
          textTransform: "uppercase",
          letterSpacing: 1,
        }}
      >
        {side === "left" ? "Before" : "After"}
      </div>
      <div style={{ padding: "4px 0" }}>
        {lines.map((entry, i) => {
          const bgColor =
            entry.type === "added"
              ? "rgba(0, 255, 0, 0.1)"
              : entry.type === "removed"
                ? "rgba(255, 0, 0, 0.1)"
                : "transparent";

          return (
            <div
              key={i}
              style={{
                display: "flex",
                height: LINE_HEIGHT,
                alignItems: "center",
                backgroundColor: bgColor,
                paddingLeft: 12,
                opacity: revealProgress,
              }}
            >
              <span
                style={{
                  width: 32,
                  textAlign: "right",
                  paddingRight: 12,
                  color: "#484f58",
                  fontSize: 12,
                  userSelect: "none",
                }}
              >
                {entry.type === "added" ? "+" : entry.type === "removed" ? "-" : " "}
              </span>
              <span
                style={{
                  color: "#c9d1d9",
                  fontSize: 14,
                  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                  whiteSpace: "pre",
                }}
              >
                {entry.line || " "}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        backgroundColor: "#0d1117",
        width: "100%",
        height: "100%",
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      }}
    >
      {renderColumn(diffOld, "left")}
      {renderColumn(diffNew, "right")}
    </div>
  );
};
