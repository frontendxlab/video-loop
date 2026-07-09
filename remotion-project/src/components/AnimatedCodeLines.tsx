import React, { useMemo, useRef, useEffect } from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from "remotion";
import { WordTiming, getStepProgress } from "../timing/audio-timing";
import { codeTheme } from "../design-tokens";

interface AnimatedCodeLinesProps {
  code: string;
  lang: string;
  wordTimestamps: WordTiming[];
  sceneStartFrame: number;
  fps?: number;
  title?: string;
}

interface Token {
  text: string;
  color: string;
}

const KEYWORDS_TS = new Set([
  "const", "let", "var", "function", "return", "if", "else", "for",
  "while", "do", "switch", "case", "break", "continue", "new", "this",
  "class", "interface", "type", "enum", "extends", "implements", "import",
  "export", "from", "as", "async", "await", "yield", "throw", "try",
  "catch", "finally", "typeof", "instanceof", "in", "of", "keyof",
  "readonly", "static", "private", "protected", "public", "abstract",
  "declare", "namespace", "module", "any", "void", "never", "unknown",
  "string", "number", "boolean", "null", "undefined", "true", "false",
]);

function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = [];
  const regex = /(\/\/(?:.*))|("(?:[^"\\]|\\.)*")|('(?:[^'\\]|\\.)*')|(`(?:[^`\\]|\\.)*`)|(\b\d+\.?\d*\b)|(\b[A-Za-z_$][\w$]*\b)|(\S)|(\s+)/g;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(line)) !== null) {
    const [full, comment, dq, sq, bt, num, ident, punct, ws] = match;
    if (comment) tokens.push({ text: comment, color: codeTheme.comment });
    else if (dq) tokens.push({ text: dq, color: codeTheme.string });
    else if (sq) tokens.push({ text: sq, color: codeTheme.string });
    else if (bt) tokens.push({ text: bt, color: codeTheme.string });
    else if (num) tokens.push({ text: num, color: codeTheme.number });
    else if (ident) {
      if (KEYWORDS_TS.has(ident)) {
        tokens.push({ text: ident, color: codeTheme.keyword });
      } else if (
        ident.length >= 2 &&
        ident[0] === ident[0]?.toUpperCase() &&
        ident[0] !== ident[0]?.toLowerCase()
      ) {
        tokens.push({ text: ident, color: codeTheme.type });
      } else if (
        ident.endsWith("(") ||
        ident.endsWith(")") ||
        ident === ident.toLowerCase()
      ) {
        tokens.push({ text: ident, color: codeTheme.function });
      } else {
        tokens.push({ text: ident, color: codeTheme.variable });
      }
    } else if (punct) {
      tokens.push({ text: punct, color: codeTheme.operator });
    } else if (ws) {
      tokens.push({ text: ws, color: codeTheme.text });
    }
  }
  return tokens;
}

export const AnimatedCodeLines: React.FC<AnimatedCodeLinesProps> = ({
  code,
  lang,
  wordTimestamps,
  sceneStartFrame,
  fps: propFps,
  title,
}) => {
  const frame = useCurrentFrame();
  const { fps: configFps } = useVideoConfig();
  const fps = propFps ?? configFps;
  const scrollRef = useRef<HTMLDivElement>(null);

  const lines = useMemo(() => code.split("\n"), [code]);
  const tokenized = useMemo(() => lines.map(tokenizeLine), [lines]);

  const hasTiming = wordTimestamps.length > 0;
  const wordsPerLine = hasTiming
    ? Math.max(1, Math.floor(wordTimestamps.length / lines.length))
    : 0;

  function getLineProgress(lineIdx: number): number {
    if (!hasTiming) {
      const stagger = lineIdx * 4;
      const local = frame - sceneStartFrame - stagger;
      if (local < 0) return 0;
      if (local >= 15) return 1;
      return local / 15;
    }
    const wordStart = Math.min(lineIdx * wordsPerLine, wordTimestamps.length - 1);
    const wordEnd = Math.min(wordStart + wordsPerLine - 1, wordTimestamps.length - 1);
    const startMs = wordTimestamps[wordStart]?.startMs ?? 0;
    const endMs = wordTimestamps[wordEnd]?.endMs ?? startMs + 500;
    return getStepProgress(frame, fps, startMs, endMs, sceneStartFrame);
  }

  function getActiveLine(): number {
    if (!hasTiming) {
      const raw = Math.floor((frame - sceneStartFrame) / 4);
      return Math.min(raw, lines.length - 1);
    }
    const currentMs = ((frame - sceneStartFrame) / fps) * 1000;
    for (let i = wordTimestamps.length - 1; i >= 0; i--) {
      if (currentMs >= wordTimestamps[i].startMs) {
        return Math.min(Math.floor(i / wordsPerLine), lines.length - 1);
      }
    }
    return -1;
  }

  const activeLine = getActiveLine();

  useEffect(() => {
    if (scrollRef.current && activeLine >= 0) {
      const container = scrollRef.current;
      const lineEl = container.children[activeLine] as HTMLElement | undefined;
      if (lineEl) {
        const containerRect = container.getBoundingClientRect();
        const lineRect = lineEl.getBoundingClientRect();
        if (
          lineRect.bottom > containerRect.bottom ||
          lineRect.top < containerRect.top
        ) {
          lineEl.scrollIntoView({ block: "center", behavior: "auto" });
        }
      }
    }
  }, [activeLine]);

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        background: "linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%)",
        width: "100%",
        height: "100%",
        overflow: "hidden",
      }}
    >
      {title && (
        <div
          style={{
            padding: "16px 24px 0",
            fontSize: 22,
            fontWeight: "600",
            color: "rgba(255,255,255,0.9)",
          }}
        >
          {title}
        </div>
      )}

      <div
        style={{
          margin: title ? "12px 24px" : "24px",
          flex: 1,
          borderRadius: 16,
          overflow: "hidden",
          background: codeTheme.background,
          border: "1px solid rgba(255,255,255,0.06)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            padding: "12px 16px",
            background: "rgba(255,255,255,0.03)",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <div
            style={{ width: 12, height: 12, borderRadius: "50%", background: "#ff5f57" }}
          />
          <div
            style={{ width: 12, height: 12, borderRadius: "50%", background: "#ffbd2e" }}
          />
          <div
            style={{ width: 12, height: 12, borderRadius: "50%", background: "#28c840" }}
          />
          <span
            style={{
              marginLeft: 12,
              fontSize: 13,
              color: "rgba(255,255,255,0.4)",
            }}
          >
            {lang}
          </span>
        </div>

        <div
          ref={scrollRef}
          style={{
            flex: 1,
            overflow: "auto",
            padding: "16px 0",
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontSize: 15,
            lineHeight: "1.7",
          }}
        >
          {tokenized.map((tokens, lineIdx) => {
            const prog = getLineProgress(lineIdx);
            const isActive = lineIdx === activeLine;
            const isPast = activeLine >= 0 && lineIdx < activeLine;

            const virtualFrame = prog * 20;
            const s = spring({
              frame: virtualFrame,
              fps: 30,
              config: { damping: 16, stiffness: 100 },
            });
            const opacity = interpolate(virtualFrame, [0, 12], [0, 1], {
              extrapolateRight: "clamp",
            });

            return (
              <div
                key={lineIdx}
                style={{
                  display: "flex",
                  opacity: isPast ? 0.5 : opacity,
                  background: isActive
                    ? "rgba(255, 235, 59, 0.08)"
                    : "transparent",
                  borderLeft: isActive
                    ? "3px solid #ffeb3b"
                    : "3px solid transparent",
                  transform: `translateX(${(1 - s) * 12}px)`,
                  padding: "1px 0",
                }}
              >
                <span
                  style={{
                    width: 40,
                    flexShrink: 0,
                    textAlign: "right",
                    marginRight: 16,
                    fontSize: 13,
                    color: isActive
                      ? "rgba(255,255,255,0.6)"
                      : codeTheme.lineNumber,
                    userSelect: "none",
                  }}
                >
                  {lineIdx + 1}
                </span>
                <span style={{ whiteSpace: "pre" }}>
                  {tokens.map((t, ti) => (
                    <span
                      key={ti}
                      style={{
                        color: isPast
                          ? "rgba(255,255,255,0.4)"
                          : t.color,
                      }}
                    >
                      {t.text}
                    </span>
                  ))}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
