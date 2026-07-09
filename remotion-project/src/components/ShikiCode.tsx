import React, { useEffect, useState } from "react";
import { continueRender, delayRender } from "remotion";
import { codeTheme, colors, fonts } from "../design-tokens";

export interface ShikiToken {
  content: string;
  color?: string;
  fontStyle?: number;
}

export interface ShikiLine {
  tokens: ShikiToken[];
}

export interface ShikiCodeProps {
  code: string;
  lang?: string;
  theme?: string;
  fontSize?: number;
  lineHeight?: number;
  highlightLines?: number[];
  visibleLines?: number;
}

const FALLBACK_LANG = "text";
const DEFAULT_THEME = "poimandres";

let highlighterPromise: Promise<any> | null = null;
let cachedHighlighter: any = null;
const loadedLangs = new Set<string>();
const loadedThemes = new Set<string>();

async function getHighlighter(lang: string, theme: string): Promise<any> {
  const shiki = await import("shiki");
  if (!cachedHighlighter) {
    cachedHighlighter = await shiki.createHighlighter({
      themes: [theme],
      langs: [lang || FALLBACK_LANG],
    });
    loadedLangs.add(lang || FALLBACK_LANG);
    loadedThemes.add(theme);
    return cachedHighlighter;
  }
  const toLoadLangs: string[] = [];
  const langKey = lang || FALLBACK_LANG;
  if (!loadedLangs.has(langKey)) toLoadLangs.push(langKey);
  const toLoadThemes: string[] = [];
  if (!loadedThemes.has(theme)) toLoadThemes.push(theme);
  if (toLoadLangs.length || toLoadThemes.length) {
    await cachedHighlighter.loadLanguage(toLoadLangs);
    await cachedHighlighter.loadTheme(toLoadThemes[0]);
    toLoadLangs.forEach((l) => loadedLangs.add(l));
    toLoadThemes.forEach((t) => loadedThemes.add(t));
  }
  return cachedHighlighter;
}

export const ShikiCode: React.FC<ShikiCodeProps> = ({
  code,
  lang = FALLBACK_LANG,
  theme = DEFAULT_THEME,
  fontSize = 16,
  lineHeight = 1.6,
  highlightLines = [],
  visibleLines,
}) => {
  const [lines, setLines] = useState<ShikiLine[] | null>(null);
  const [handle] = useState(() => delayRender("Loading shiki highlighter"));

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const hl = await getHighlighter(lang, theme);
        const result = hl.codeToTokens(code, { lang: lang || FALLBACK_LANG, theme });
        if (cancelled) return;
        setLines(result.tokens as ShikiLine[]);
      } catch (err) {
        if (cancelled) return;
        setLines(code.split("\n").map((l) => [{ content: l || " " }]));
      } finally {
        continueRender(handle);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [code, lang, theme, handle]);

  if (!lines) {
    return (
        <div style={{ fontFamily: fonts.mono, fontSize, color: colors.textMuted }}>
        Loading…
      </div>
    );
  }

  const shown = visibleLines != null ? lines.slice(0, visibleLines) : lines;

  return (
    <div style={{ fontFamily: fonts.mono, fontSize, lineHeight }}>
      {shown.map((line, i) => {
        const isHighlighted = highlightLines.includes(i + 1);
        return (
          <div
            key={i}
            style={{
              display: "flex",
               background: isHighlighted ? codeTheme.highlightBg : "transparent",
               borderLeft: isHighlighted ? `3px solid ${colors.primary}` : "3px solid transparent",
            }}
          >
            <span
              style={{
                width: 36,
                 color: codeTheme.lineNumber,
                textAlign: "right",
                marginRight: 16,
                flexShrink: 0,
                fontSize: fontSize - 2,
              }}
            >
              {i + 1}
            </span>
            <span style={{ whiteSpace: "pre" }}>
              {line.length === 0
                ? " "
                : line.map((tok, j) => (
                    <span key={j} style={{ color: tok.color || "#fff" }}>
                      {tok.content || " "}
                    </span>
                  ))}
            </span>
          </div>
        );
      })}
    </div>
  );
};
