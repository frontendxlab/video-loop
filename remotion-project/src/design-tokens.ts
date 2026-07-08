export const colors = {
  black: "#000000",
  white: "#FFFFFF",
  primary: "#6C63FF",
  secondary: "#FF6584",
  background: "#0D1117",
  surface: "#161B22",
  text: "#E6EDF3",
  textMuted: "#8B949E",
  accent: "#58A6FF",
  success: "#3FB950",
  warning: "#D29922",
  error: "#F85149",
  diffAdded: "rgba(0, 255, 0, 0.1)",
  diffAddedBorder: "rgba(0, 255, 0, 0.3)",
  diffRemoved: "rgba(255, 0, 0, 0.1)",
  diffRemovedBorder: "rgba(255, 0, 0, 0.3)",
} as const;

export const fonts = {
  sans: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
  heading: "Inter, sans-serif",
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  section: 64,
} as const;

export const codeTheme = {
  background: "#1E1E1E",
  text: "#D4D4D4",
  keyword: "#569CD6",
  string: "#CE9178",
  number: "#B5CEA8",
  comment: "#6A9955",
  function: "#DCDCAA",
  variable: "#9CDCFE",
  type: "#4EC9B0",
  operator: "#D4D4D4",
  lineNumber: "#858585",
  highlightBg: "rgba(255, 255, 255, 0.06)",
} as const;
