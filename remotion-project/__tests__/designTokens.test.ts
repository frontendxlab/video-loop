import { describe, expect, it } from "vitest";

import rawTokens from "../../config/design-tokens.json";
import {
  animotionTheme, chart, codeTheme, colors, device, fonts,
  glass, hud, remotionStyleDefaults, showcase, spacing,
} from "../src/design-tokens";

describe("shared design tokens", () => {
  it("loads root token file into Remotion helpers", () => {
    expect(colors.primary).toBe(rawTokens.theme.primaryColor);
    expect(fonts.monoFamily).toBe(rawTokens.fonts.mono.family);
    expect(codeTheme.shikiTheme).toBe(rawTokens.code.theme.name);
  });

  it("keeps Remotion and Animotion defaults aligned", () => {
    expect(remotionStyleDefaults.primaryColor).toBe(animotionTheme.accentColor);
    expect(remotionStyleDefaults.font).toBe(animotionTheme.bodyFont);
    expect(remotionStyleDefaults.codeTheme).toBe(animotionTheme.codeTheme);
  });

  it("maps all code theme colors from raw tokens", () => {
    const t = rawTokens.code.theme;
    expect(codeTheme.background).toBe(t.background);
    expect(codeTheme.text).toBe(t.text);
    expect(codeTheme.keyword).toBe(t.keyword);
    expect(codeTheme.string).toBe(t.string);
    expect(codeTheme.number).toBe(t.number);
    expect(codeTheme.comment).toBe(t.comment);
    expect(codeTheme.function).toBe(t.function);
    expect(codeTheme.variable).toBe(t.variable);
    expect(codeTheme.type).toBe(t.type);
    expect(codeTheme.operator).toBe(t.operator);
    expect(codeTheme.lineNumber).toBe(t.lineNumber);
    expect(codeTheme.highlightBg).toBe(t.highlightBg);
    expect(codeTheme.activeBorder).toBe(t.activeBorder);
  });

  it("maps all color surface values from raw tokens", () => {
    const t = rawTokens.theme;
    expect(colors.background).toBe(t.background.base);
    expect(colors.backgroundElevated).toBe(t.background.elevated);
    expect(colors.surface).toBe(t.background.surface);
    expect(colors.text).toBe(t.text.primary);
    expect(colors.textMuted).toBe(t.text.muted);
    expect(colors.secondary).toBe(t.accent.secondary);
    expect(colors.success).toBe(t.accent.success);
    expect(colors.error).toBe(t.accent.error);
    expect(colors.diffAdded).toBe(t.diff.added);
    expect(colors.diffAddedBorder).toBe(t.diff.addedBorder);
    expect(colors.diffRemoved).toBe(t.diff.removed);
    expect(colors.diffRemovedBorder).toBe(t.diff.removedBorder);
  });

  it("maps all font values from raw tokens", () => {
    expect(fonts.bodyFamily).toBe(rawTokens.fonts.body.family);
    expect(fonts.headingFamily).toBe(rawTokens.fonts.heading.family);
    expect(fonts.sans).toBe(rawTokens.fonts.body.stack);
    expect(fonts.heading).toBe(rawTokens.fonts.heading.stack);
    expect(fonts.mono).toBe(rawTokens.fonts.mono.stack);
  });

  it("maps spacing from raw tokens", () => {
    expect(spacing.xs).toBe(rawTokens.spacing.xs);
    expect(spacing.sm).toBe(rawTokens.spacing.sm);
    expect(spacing.md).toBe(rawTokens.spacing.md);
    expect(spacing.lg).toBe(rawTokens.spacing.lg);
    expect(spacing.xl).toBe(rawTokens.spacing.xl);
    expect(spacing.xxl).toBe(rawTokens.spacing.xxl);
    expect(spacing.section).toBe(rawTokens.spacing.section);
  });

  it("animotionTheme matches raw token section exactly", () => {
    const expected = rawTokens.animotion.theme;
    expect(animotionTheme.deckBackground).toBe(expected.deckBackground);
    expect(animotionTheme.panelBackground).toBe(expected.panelBackground);
    expect(animotionTheme.textColor).toBe(expected.textColor);
    expect(animotionTheme.accentColor).toBe(expected.accentColor);
    expect(animotionTheme.codeTheme).toBe(expected.codeTheme);
    expect(animotionTheme.headingFont).toBe(expected.headingFont);
    expect(animotionTheme.bodyFont).toBe(expected.bodyFont);
    expect(animotionTheme.monoFont).toBe(expected.monoFont);
  });

  it("hud tokens match raw tokens", () => {
    const h = rawTokens.hud;
    expect(hud.scanline).toBe(h.scanline);
    expect(hud.grid).toBe(h.grid);
    expect(hud.reticle).toBe(h.reticle);
    expect(hud.reticleOpacity).toBe(h.reticleOpacity);
    expect(hud.cornerBracket).toBe(h.cornerBracket);
    expect(hud.dataReadout.background).toBe(h.dataReadout.background);
    expect(hud.dataReadout.border).toBe(h.dataReadout.border);
    expect(hud.dataReadout.label).toBe(h.dataReadout.label);
    expect(hud.dataReadout.value).toBe(h.dataReadout.value);
    expect(hud.dataReadout.accent).toBe(h.dataReadout.accent);
  });

  it("glass tokens match raw tokens", () => {
    const g = rawTokens.glass;
    expect(glass.backdropBlur).toBe(g.backdropBlur);
    expect(glass.background).toBe(g.background);
    expect(glass.border).toBe(g.border);
    expect(glass.highlight).toBe(g.highlight);
    expect(glass.shadow).toBe(g.shadow);
    expect(glass.borderRadius).toBe(g.borderRadius);
  });

  it("device tokens match raw tokens", () => {
    const d = rawTokens.device;
    expect(device.phone.bezel).toBe(d.phone.bezel);
    expect(device.phone.shadow).toBe(d.phone.shadow);
    expect(device.tablet.bezel).toBe(d.tablet.bezel);
    expect(device.tablet.shadow).toBe(d.tablet.shadow);
    expect(device.laptop.bezel).toBe(d.laptop.bezel);
    expect(device.laptop.shadow).toBe(d.laptop.shadow);
    expect(device.monitor.bezel).toBe(d.monitor.bezel);
    expect(device.monitor.shadow).toBe(d.monitor.shadow);
  });

  it("chart tokens match raw tokens", () => {
    const c = rawTokens.chart;
    expect(chart.gridLine).toBe(c.gridLine);
    expect(chart.axisLine).toBe(c.axisLine);
    expect(chart.axisLabel).toBe(c.axisLabel);
    expect(chart.series).toEqual(c.series);
    expect(chart.areaFill).toBe(c.areaFill);
    expect(chart.barRadius).toBe(c.barRadius);
    expect(chart.dotRadius).toBe(c.dotRadius);
    expect(chart.lineWidth).toBe(c.lineWidth);
  });

  it("showcase tokens match raw tokens", () => {
    const s = rawTokens.showcase;
    expect(showcase.overlayGradient).toBe(s.overlayGradient);
    expect(showcase.heroOverlay).toBe(s.heroOverlay);
    expect(showcase.cta.background).toBe(s.cta.background);
    expect(showcase.cta.text).toBe(s.cta.text);
    expect(showcase.cta.borderRadius).toBe(s.cta.borderRadius);
    expect(showcase.cta.shadow).toBe(s.cta.shadow);
    expect(showcase.accentGlow).toBe(s.accentGlow);
    expect(showcase.particle).toBe(s.particle);
    expect(showcase.sparkle).toBe(s.sparkle);
  });
});
