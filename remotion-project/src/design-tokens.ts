import tokens from "../../config/design-tokens.json";

export const designTokens = tokens;

export const colors = {
  black: "#000000",
  white: "#FFFFFF",
  primary: tokens.theme.primaryColor,
  secondary: tokens.theme.accent.secondary,
  background: tokens.theme.background.base,
  backgroundElevated: tokens.theme.background.elevated,
  backgroundGradient: tokens.theme.background.gradient,
  panelGradient: tokens.theme.background.panelGradient,
  surface: tokens.theme.background.surface,
  text: tokens.theme.text.primary,
  textMuted: tokens.theme.text.muted,
  textSubtle: tokens.theme.text.subtle,
  accent: tokens.theme.accent.info,
  success: tokens.theme.accent.success,
  warning: tokens.theme.accent.warning,
  error: tokens.theme.accent.error,
  highlight: tokens.theme.accent.highlight,
  diffAdded: tokens.theme.diff.added,
  diffAddedBorder: tokens.theme.diff.addedBorder,
  diffRemoved: tokens.theme.diff.removed,
  diffRemovedBorder: tokens.theme.diff.removedBorder,
  chromeBorder: tokens.theme.chrome.border,
  chromePanel: tokens.theme.chrome.panel,
  chromeDotRed: tokens.theme.chrome.dotRed,
  chromeDotYellow: tokens.theme.chrome.dotYellow,
  chromeDotGreen: tokens.theme.chrome.dotGreen,
} as const;

export const fonts = {
  sans: tokens.fonts.body.stack,
  mono: tokens.fonts.mono.stack,
  heading: tokens.fonts.heading.stack,
  bodyFamily: tokens.fonts.body.family,
  monoFamily: tokens.fonts.mono.family,
  headingFamily: tokens.fonts.heading.family,
} as const;

export const spacing = tokens.spacing;

export const codeTheme = {
  background: tokens.code.theme.background,
  text: tokens.code.theme.text,
  keyword: tokens.code.theme.keyword,
  string: tokens.code.theme.string,
  number: tokens.code.theme.number,
  comment: tokens.code.theme.comment,
  function: tokens.code.theme.function,
  variable: tokens.code.theme.variable,
  type: tokens.code.theme.type,
  operator: tokens.code.theme.operator,
  lineNumber: tokens.code.theme.lineNumber,
  highlightBg: tokens.code.theme.highlightBg,
  activeBorder: tokens.code.theme.activeBorder,
  shikiTheme: tokens.code.theme.name,
} as const;

export const remotionStyleDefaults = {
  primaryColor: tokens.theme.primaryColor,
  font: tokens.fonts.body.family,
  codeTheme: tokens.code.theme.name,
} as const;

export const animotionTheme = tokens.animotion.theme;
